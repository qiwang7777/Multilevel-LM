import torch
import torch.nn as nn
import numpy as np



class FullyConnectedNN(nn.Module):
    def __init__(self, input_size, n_hidden_layers, r_nodes_per_layer, output_size, activation_function=nn.ReLU()):
        super(FullyConnectedNN, self).__init__()
        self.hidden_layers = nn.ModuleList()
        self.activation_function = activation_function
        
        # Input layer (first hidden layer)
        self.hidden_layers.append(nn.Linear(input_size, r_nodes_per_layer))
        
        # Additional hidden layers
        for _ in range(1, n_hidden_layers):
            self.hidden_layers.append(nn.Linear(r_nodes_per_layer, r_nodes_per_layer))
        
        # Output layer
        self.output_layer = nn.Linear(r_nodes_per_layer, output_size)
    
    def forward(self, x):
        for layer in self.hidden_layers:
            x = self.activation_function(layer(x))
        x = self.output_layer(x)
        return x
  
    
#Test and usage of FullyConnectedNN

# Network configuration
#input_dim = 1
#output_dim = 1
#n_hidden_layers = 1
#r_nodes_per_layer = 500
#activation_function = torch.sigmoid

# Create the network
#My_model = FullyConnectedNN(input_dim, n_hidden_layers, r_nodes_per_layer, output_dim, activation_function)

# Manually set the weights and biases, which is generated by random numbers
#weights = [
#    np.random.randn(r_nodes_per_layer, input_dim),          # First hidden layer
#    np.random.randn(output_dim, r_nodes_per_layer)          # Output layer
#]

#biases = [
#    np.random.randn(r_nodes_per_layer),  # First hidden layer
#    np.random.randn(output_dim)          # Output layer
#]

#Save the weights and biases into some files, make sure each time we use the same values for them for testing
#np.savez('weights_file.npz',*weights)
#np.savez('biases_file.npz',*biases)
#data_weights = np.load('weights_file.npz')
#fixed_weights = [data_weights[key] for key in sorted(data_weights.files)]
#data_biases = np.load('biases_file.npz')
#fixed_biases = [data_biases[key] for key in sorted(data_biases.files)]
#with torch.no_grad():
    # Set weights and biases for the first hidden layer
#    My_model.hidden_layers[0].weight = nn.Parameter(torch.tensor(fixed_weights[0], dtype=torch.float32))
#    My_model.hidden_layers[0].bias = nn.Parameter(torch.tensor(fixed_biases[0], dtype=torch.float32))
#
    # Set weights and biases for the remaining hidden layers
#    for i in range(1, n_hidden_layers):
#        My_model.hidden_layers[i].weight = nn.Parameter(torch.tensor(fixed_weights[i], dtype=torch.float32))
#        My_model.hidden_layers[i].bias = nn.Parameter(torch.tensor(fixed_biases[i], dtype=torch.float32))

    # Set weights and biases for the output layer
#    My_model.output_layer.weight = nn.Parameter(torch.tensor(fixed_weights[-1], dtype=torch.float32))
#    My_model.output_layer.bias = nn.Parameter(torch.tensor(fixed_biases[-1], dtype=torch.float32))
    
# Generate some random input data with sample number
#sample_num = 41
#input_data = torch.tensor(np.linspace(0,1,sample_num).reshape(sample_num,input_dim), dtype=torch.float32)

# Forward pass through the network
#output = My_model(input_data)
