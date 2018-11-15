import struct
import binascii
import sys

class Node:
	# Used to build the Huffman tree
	name = ""
	value = 0
	child1 = None
	child2 = None	

	def nprint(self):
		# A recursive function that prints out the name of the node, then the child nodes. 
		print("Name: "+self.name+", value: "+str(self.value))
		if self.child1 != None:
			self.child1.nprint()
		if self.child2 != None:
			self.child2.nprint()

	def generate_binary(self, starting_value):
		# A recursive function that generates the binary string for all leaves underneath it.
		leaves = []
		if len(self.name) == 1: # We are a leaf because the name length is only 1 character long
			leaves.append((self.name, starting_value))
		else:
			if self.child1 != None:
				leaves += self.child1.generate_binary(starting_value+"0")
			if self.child2 != None:
				leaves += self.child2.generate_binary(starting_value+"1")
		return leaves

def convert_to_binary_string(value, starting_bit):
	# Used to convert a decimal value to a binary string of variable length
	if starting_bit == 0:
		return ""
	if ((value - pow(2,starting_bit - 1)) >= 0):
		return "1"+convert_to_binary_string(value - pow(2,starting_bit - 1), starting_bit- 1)
	else:
		return "0"+convert_to_binary_string(value, starting_bit - 1)

def convert_to_char_from_binary(binary):
	# Used to convert a binary string back into a character value
	value = 0
	for i in range(len(binary)):
		value += int(binary[i]) * pow(2, 7 - i)
	return value


def compress(filename, outfile):
	# Main function used to compress text
	print("Preparing to compress " + filename + " using Huffman Coding")
	file = open(filename)
	text = ""
	# Read contents of file into memory...
	for line in file:
		text += line

	chars = {}
	# Generate a dictionary of individual keys and they frequencies...
	for char in text:
		if char in chars:
			chars[char] += 1
		else:
			chars[char] = 1

	sorted_list = []
	# Create a sorted list of tuples based on the dictionary of character keys
	for key, value in sorted(chars.iteritems(), key=lambda (k,v): (v,k), reverse=True):
		sorted_list.append((key, value))
	print("Character dictionary generated, size: " + str(len(chars)) + ".")

	# Construct initial nodes
	nodes = []
	for key,value in sorted_list:
		n = Node()
		n.name = key
		n.value = value
		nodes.append(n)
	print("Initial nodes created and populated with keys.")
	print("Preparing to generate tree...")

	# Build the tree
	while(len(nodes) > 1):
		# Get rid of the bottom two nodes...
		bottom_node_1 = nodes.pop()
		bottom_node_2 = nodes.pop()

		# Create a new node and populate it with information from the two nodes that were popped...
		new_node = Node()
		new_node.name = bottom_node_1.name + bottom_node_2.name
		new_node.value = bottom_node_1.value + bottom_node_2.value
		new_node.child1 = bottom_node_1
		new_node.child2 = bottom_node_2

		# Find where to insert the newly created tree...
		inserted = 0
		for i in range(len(nodes)):
			if nodes[i].value <= new_node.value:
				nodes.insert(i, new_node) # insert the newly created node into the tree
				inserted = 1 # Mark it as inserted
				break
		if inserted == 0:
			# If it was never inserted into the list, it means it was lower than any other values so we just add it to the end
			nodes.append(new_node)

	# Set root node to the only node left in the list
	root = nodes[0] 
	print("Tree completed.")

	# Now we want to generate the binary value for each character
	binary_characters = root.generate_binary("")
	binary_characters_dict = {}

	# We've created a list of tuples of characters and their binary representations.
	# Now we want to convert it to a dictionary.
	for key,value in binary_characters:
		binary_characters_dict[key] = value
	print("Binary numbers generated for each leaf node.\nPreparing to compress text.")


	# Now let's actually compress the text!
	compressed_text = ""
	for character in text:
		compressed_text += binary_characters_dict[character]
	print("Text compression complete.\nPreparing to convert key to binary.")
	# Alright, text converted into binary and concatenated into one string!

	# Now we need to convert the key to binary as well in order to be able to insert it into the same file as the compressed data
	# First compress the key into a single string
	total_key = ""
	for character, value in binary_characters:
		total_key += character + ":" +value + ","

	# Generate the binary encoding of the key
	total_key = total_key[:-1] # Get rid of the last comma
	binary_key = ""
	char_might_be_semicolon = 0 # Flag to see if the character is a semicolon or just a separator
	for char in total_key:
		if char == ":": # If the character is a potential separator...
			if char_might_be_semicolon == 1: # We have encountered 2 semicolons in a row, meaning a semicolon was the key
				binary_key += convert_to_binary_string(ord(char),8)+ "10000000"  # Add the binary version of the character and an unusable value to the binary_key as a separator 
				char_might_be_semicolon = 0
			else: # This might be a separator but we're not sure, so don't add anything yet.
				char_might_be_semicolon = 1 
		else:
			if char_might_be_semicolon == 1:
				binary_key += "10000000" # The last character was a separator but we did not add it to the binary_key, let's do it now
			char_might_be_semicolon = 0
			binary_key += convert_to_binary_string(ord(char),8) # Add the binary version of the character to the binary_key
	
	i = 0
	extracted_key = ""
	while(i < len(binary_key)):
		extracted_key += chr(convert_to_char_from_binary(binary_key[i:8+i]))
		i += 8

	print("Key converted successfully.")

	# Ok, now we have the key in binary form and we need to create the total binary string
	total_binary = binary_key + "00000000" + compressed_text

	# Now we have to make sure that it's a multiple of 8 so when we convert it to bits, it won't have any overflow or underflow.
	print("In order to store the file as bytes, we need to ensure the total length is a multiple of 8.")
	print("Length: " + str(len(total_binary)))
	padding_count = (8 - (len(total_binary) % 8)) % 8
	print("Padding required: " + str(padding_count))
	padding = ""
	if padding_count < 8:
		for i in range(padding_count):
			padding += "0"
	last_byte = convert_to_binary_string(padding_count, 8)
	padding_count = padding_count % 8
	print("Padding: " + padding)
	print("We have to add another final byte to store the number of bits used for padding")
	print("Last byte: " + last_byte)
	total_binary += padding
	total_binary += last_byte
	
	x = 0
	byte_list = []
	print("Preparing to convert bits to bytes...")
	while(x < len(total_binary)):
		byte_string = total_binary[x:x+8]
		byte = int(byte_string,2)
		byte_list.append(byte)
		#print(byte_string)
		x += 8
	f = open(outfile,"wb")
	print("Successfully created byte array.\nPreparing to write byte array to file...")
	binary_format = bytearray(byte_list)
	f.write(binary_format)
	f.close()
	print("Succesfully stored bytes in file.")
	print("Length of total text in chars: \t" + str(len(text)))
	print("Length of compressed binary in bytes: \t" + str(len(total_binary)/8))
	print("Compression ratio: " + str(int((float((len(total_binary)/8)) / float(len(text)))*100)) + "%")
	print("Compression complete!")
	print("Compressed file saved as: " + outfile + '\n\n')

def decompress(source_file, dest_file):
	print("Preparing to decompress file.")
	file = open(source_file, "rb")
	binary_list = []
	with file:
		byte = file.read(1)
		while byte:
			hexadecimal = binascii.hexlify(byte)
			decimal = int(hexadecimal, 16)
			binary = bin(decimal)[2:].zfill(8)
			byte = file.read(1)
			binary_list.append(binary)
	print("Binary file successfully loaded.")
	key_dict = {}
	key_string = ""
	binary_repr = ""
	value = ""
	data_boundary_index = 0
	for item in binary_list:
		if item == "00000000":
			break
		data_boundary_index += 1
		if item == "00110000":
			# Item is a zero
			binary_repr += "0"
		elif item == "00110001":
			# Item is a one
			binary_repr += "1"
		elif item == "10000000":
			# Item is a divider
			nothing = 1
		else: 
			# Item must be the char value
			if value != "":
				key_dict[binary_repr] = value
				binary_repr = ""
			value = chr(int(item,2))
		#print("char: " + chr(int(item,2)) + ", binary: " + item)
	key_dict[binary_repr] = value
	# Ok, now we have a dictionary of the keys, and we have the index of where the data starts. 
	binary_list = binary_list[data_boundary_index + 1:]
	print("Key dictionary generated from beginning part of file. ")

	# Before we start decompressing the data, we first need to strip the last byte off and check how many bits should be included in the second to last byte
	padding = int(binary_list.pop(),2)
	binary_list[-1] = binary_list[-1][:(padding * -1)]
	print("Number of bits used to pad end of compressed file: " + str(padding))

	# Now we can put all of the binary data into one string and begin matching it to the keys
	binary_string = ""
	for item in binary_list:
		binary_string += item

	print("Binary data concatenated into single string.\nPreparing to decompress binary stream...")
	# Now let's actually run through and decode the string!
	decoded_text = ""
	curr_repr = ""
	i = 0
	outfile = open(dest_file, "w")
	while i < len(binary_string):
		curr_repr += binary_string[i]
		if curr_repr in key_dict:
			decoded_text += key_dict[curr_repr]
			outfile.write(key_dict[curr_repr])
			curr_repr = ""
		i += 1
	print("Decompression complete!")
	print("Decompressed text stored in " + dest_file)

def main():
	if len(sys.argv) < 3:
		print("Incorrect usage\nCorrect usage:\n\tCompression:\n\t\thuffman_coding.py compress <input_file> <output_file>\n\tDecompression:\n\t\thuffman_coding.py decompress <input_file> <output_file>\n")
	elif sys.argv[1] == "compress":
		compress(sys.argv[2],sys.argv[3])
	elif sys.argv[1] == "decompress":
		decompress(sys.argv[2],sys.argv[3])
	else:
		print("Incorrect usage\nCorrect usage:\n\tCompression:\n\t\thuffman_coding.py compress <input_file> <output_file>\n\tDecompression:\n\t\thuffman_coding.py decompress <input_file> <output_file>\n")


if __name__ == "__main__":
	main()