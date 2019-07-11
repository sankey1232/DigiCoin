import datetime
import hashlib
import json
from flask import Flask, jsonify, request
import requests
from uuid import uuid4
from urllib.parse import urlparse

# Part 1- Cryptocurrency blockchain architecture
class Blockchain:
    def __init__(self):
        self.chain = []
        self.transactions = []
        self.create_block(proof = 1, previous_hash = '0')
        self.nodes = set()


    def create_block(self, proof, previous_hash):
        block={'index':len(self.chain)+1,
               'timestamp':str(datetime.datetime.now()),
               'proof':proof,
               'transactions':self.transactions,
               'previous_hash':previous_hash}
        self.transactions = []
        self.chain.append(block)
        return block

    '''Returns the end block of the current chain which acts as
        a previous block for the block to be added'''
    def get_previous_block(self): 
        return self.chain[-1]

    def proof_of_work(self, previous_proof):
        new_proof = 1
        check_proof = False
        while check_proof is False:
            hash_generation = hashlib.sha256(str(new_proof**2-previous_proof**2).encode()).hexdigest()
            if hash_generation[:4]=='0000':
                check_proof = True
            else:
                new_proof+=1
        return new_proof
    
    def generate_hash(self, block):
        encoded_block = json.dumps(block, sort_keys=True).encode()
        hash = hashlib.sha256(encoded_block).hexdigest()
        return hash

    def chain_validation(self, chain):
        previous_block = chain[0]
        block_index = 1
        while block_index < len(chain):
            block = chain[block_index]
            if block['previous_hash'] != self.generate_hash(previous_block):
                return False
            previous_proof = previous_block['proof']
            proof = block['proof']
            hash_generation = hashlib.sha256(str(proof**2-previous_proof**2).encode()).hexdigest()
            if hash_generation[:4] != '0000':
                return False
            previous_block = block
            block_index+=1
        return True

    def add_transaction(self, sender, receiver, amount):
        self.transactions.append({'sender': sender,
                                  'receiver': receiver,
                                  'amount': amount })
        previous_block = self.get_previous_block()
        return previous_block['index'] + 1

    def add_node(self , address):
        parsed_url = urlparse(address)
        self.nodes.add(parsed_url.netloc)

    def replace_chain(self):
        network = self.nodes
        largest_chain = None
        max_length = len(self.chain)
        for node in network:
            response = requests.get(f'http://{node}/get_chain')
            if response.status_code == 200:
                length = response.json()['length']
                chain = response.json()['chain']
            if length > max_length and self.chain_validation(chain):
                max_length = length
                largest_chain = chain
        if largest_chain:
            self.chain = largest_chain
            return True
        return False

# Part 2- Interactive web interface for blockchain
app = Flask(__name__)
node_address = str(uuid4()).replace('-','')
bc = Blockchain()
    
# Mining a new block
@app.route('/mine_block', methods=['GET'])
def mine_block():
    previous_block = bc.get_previous_block()
    previous_proof = previous_block['proof']
    proof = bc.proof_of_work(previous_proof)
    bc.add_transaction(node_address , 'Me' , 10)
    previous_hash = bc.generate_hash(previous_block)
    block = bc.create_block(proof, previous_hash)
    response = {'Message': 'Congratulations, you just mined a new block!',
                'index':block['index'],
                'timestamp':block['timestamp'],
                'proof':block['proof'],
                'transactions': block['transactions'],
                'previous_hash':block['previous_hash']}
    return jsonify(response), 200

# Displaying the whole blockchain
@app.route('/get_chain', methods=['GET'])
def get_chain():
    response={'chain':bc.chain, 'length':len(bc.chain)}
    return jsonify(response), 200

# Checking if the blockchain is valid
@app.route('/is_valid', methods=['GET'])
def is_valid():
    validity = bc.chain_validation(bc.chain)
    if validity:
        response = {'Message':'The blockchain is valid'}
    else:
        response = {'Message':'There are problems in the blockchain'}
    return jsonify(response), 200

# Adding a new transaction to the blockchain
@app.route('/add_transaction', methods = ['POST'])
def add_transaction():
    json = request.get_json()
    transaction_keys = ['sender','receiver','amount']
    if not all (key in json for key in transaction_keys):
      return 'Some keys are missing!' , 400
    index = bc.add_transaction(json['sender'], json['receiver'], json['amount'])
    response = {'message' : f'This transaction will be added to block {index}'}
    return jsonify(response), 201

# Connecting new nodes to the network
@app.route('/connect_node', methods = ['POST'])
def connect_node():
    json = request.get_json()
    nodes = json.get('nodes')
    if nodes is None:
        return 'No nodes to add', 400
    for node in nodes:
        bc.add_node(node)
    response = {'message': 'All the nodes are now connected. The DigiCoin network now consists of the following nodes:',
                'total_nodes': list(bc.nodes)}
    return jsonify(response), 201
    
# Replacing the chain by the longest chain if needed
@app.route('/replace_chain', methods = ['GET'])
def replace_chain():
    is_chain_replaced = bc.replace_chain()
    if is_chain_replaced:
        response = {'message': 'The nodes had different chains so it was replaced by the longest chain.',
                    'new_chain': bc.chain}
    else:
        response = {'message': 'All good. No chain replacement needed.',
                    'actual_chain': bc.chain}
    return jsonify(response), 200


# Running the app
app.run(host = '0.0.0.0', port = 5001)








    
