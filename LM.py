#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
import torch
import torch.nn as nn
import numpy as np
import torch.autograd as autograd
import autograd.numpy as np
from autograd import grad, jacobian, hessian
from autograd import elementwise_grad

from scipy.sparse.linalg import cg


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

# Network configuration
input_dim = 1
output_dim = 1
n_hidden_layers = 1
r_nodes_per_layer = 5
activation_function = torch.sigmoid

# Create the network
My_model = FullyConnectedNN(input_dim, n_hidden_layers, r_nodes_per_layer, output_dim, activation_function)

# Manually set the weights and biases, which is generated by random numbers
weights = [
    np.random.randn(r_nodes_per_layer, input_dim),          # First hidden layer
    np.random.randn(output_dim, r_nodes_per_layer)          # Output layer
]

biases = [
    np.random.randn(r_nodes_per_layer),  # First hidden layer
    np.random.randn(output_dim)          # Output layer
]

#Save the weights and biases into some files, make sure each time we use the same values for them for testing
np.savez('weights_file.npz',*weights)
np.savez('biases_file.npz',*biases)
data_weights = np.load('weights_file.npz')
fixed_weights = [data_weights[key] for key in sorted(data_weights.files)]
data_biases = np.load('biases_file.npz')
fixed_biases = [data_biases[key] for key in sorted(data_biases.files)]
with torch.no_grad():
    # Set weights and biases for the first hidden layer
    My_model.hidden_layers[0].weight = nn.Parameter(torch.tensor(fixed_weights[0], dtype=torch.float32))
    My_model.hidden_layers[0].bias = nn.Parameter(torch.tensor(fixed_biases[0], dtype=torch.float32))

    # Set weights and biases for the remaining hidden layers
    for i in range(1, n_hidden_layers):
        My_model.hidden_layers[i].weight = nn.Parameter(torch.tensor(fixed_weights[i], dtype=torch.float32))
        My_model.hidden_layers[i].bias = nn.Parameter(torch.tensor(fixed_biases[i], dtype=torch.float32))

    # Set weights and biases for the output layer
    My_model.output_layer.weight = nn.Parameter(torch.tensor(fixed_weights[-1], dtype=torch.float32))
    My_model.output_layer.bias = nn.Parameter(torch.tensor(fixed_biases[-1], dtype=torch.float32))


# Generate some random input data with sample number
sample_num = 40
input_data = torch.tensor(np.linspace(0,1,sample_num).reshape(sample_num,input_dim), dtype=torch.float32)

# Forward pass through the network
output = My_model(input_data)


#Calculte the gradient and second derivative of NN w.r.t. input x
def compute_first_derivative(model,input_data):
    input_data.requires_grad = True

    # Forward pass: Compute the network output
    output = model(input_data)

    # First derivative: Compute the gradient of the output with respect to the input
    first_derivative = torch.autograd.grad(outputs=output, inputs=input_data,
                                           grad_outputs=torch.ones_like(output),
                                           create_graph=True, allow_unused=True)[0]
    return first_derivative
    
#Test for function compute_first_derivative
#print(compute_first_derivative(My_model, input_data))
#it works
def compute_second_derivative(model, input_data):
    input_data.requires_grad = True


    # First derivative: Compute the gradient of the output with respect to the input
    first_derivative = compute_first_derivative(model, input_data)

    if first_derivative is None:
        return ValueError("First derivative is None. Check if the input tensor is used in the graph.")


    # Second derivative: Compute the gradient of the first derivative with respect to the input
    second_derivative = torch.zeros_like(input_data)
    for i in range(input_data.size(0)):  # Iterate over input features
        grad2 = torch.autograd.grad(first_derivative[i], input_data, retain_graph=True, allow_unused=True)[0]
        if grad2 is not None:
            second_derivative[i] = grad2[i]

    return second_derivative
#Test for function compute_second_derivative
#print(compute_second_derivative(My_model, input_data))
#it works

#Define the loss function

#Define the PDE class first

from scipy.sparse import diags, kron, eye

class PDE:
    def __init__(self, domain, real_solution=None):
        self.domain = domain
        self.real_solution = real_solution

    def laplacian_1d(self, grid_points):
        n = len(grid_points)
        dx = grid_points[1] - grid_points[0]
        diagonals = [-2 * np.ones(n), np.ones(n - 1), np.ones(n - 1)]
        L = diags(diagonals, [0, -1, 1], shape=(n, n), format='csr')
        L /= dx**2
        return L




    def laplacian_2d(self,x_grid, y_grid):
        """
        Create a 2D Laplacian matrix for the given x and y grids.
    
        Parameters:
        x_grid (np.ndarray): 1D array representing the x-coordinates of the grid.
        y_grid (np.ndarray): 1D array representing the y-coordinates of the grid.
    
        Returns:
        scipy.sparse.csr_matrix: The Laplacian matrix for the given grid.
        """
        n_x = x_grid.size
        n_y = y_grid.size
    
        # Compute grid spacing (assume uniform grid)
        dx = x_grid[1] - x_grid[0]
        dy = y_grid[1] - y_grid[0]
    
        # Create 1D Laplacian matrices for x and y directions
        D_x = diags([1, -2, 1], [1, 0, -1], shape=(n_x, n_x)) / dx**2
        D_y = diags([1, -2, 1], [1, 0, -1], shape=(n_y, n_y)) / dy**2
        I_x = eye(n_x)
        I_y = eye(n_y)
    
        # Create the 2D Laplacian using Kronecker product
        L = kron(I_y, D_x) + kron(D_y, I_x)
    
        return L






    def compute_source_term_DD(self, grid_points, real_solution):
        if isinstance(grid_points, tuple):  # 2D case
            x_grid, y_grid = grid_points
            X,Y = np.meshgrid(x_grid,y_grid)
            L = self.laplacian_2d(x_grid, y_grid)
            u = real_solution(X, Y).ravel()  # Flatten 2D array to 1D
            if L.shape[0] != u.shape[0]:
                raise ValueError("Dimension mismatch between Laplacian and real solution.")
            source_term = L.dot(u)
        else:  # 1D case
            L = self.laplacian_1d(grid_points)
            u = real_solution(grid_points)
            if L.shape[0] != u.shape[0]:
                raise ValueError("Dimension mismatch between Laplacian and real solution.")
            source_term = L.dot(u)
        
        return torch.tensor(source_term)
    
    def compute_source_term(self, grid_points, solution):
        # This should be a PyTorch tensor operation, assume solution is also a torch function
        return torch.tensor([solution(x).item() for x in grid_points], dtype=torch.float32) 

# Define the real solution functions
def real_solution_1d(x):
    return torch.sin(x)

def real_solution_2d(x, y):
    return x**2 + y**2

def model_nn(x,model=My_model):
    x = torch.tensor(x, dtype=torch.float32).reshape(-1,1)
    return model(x).detach().numpy()

# Example usage for 1D:
domain_1d = (0, 1)
grid_points_1d = np.linspace(domain_1d[0], domain_1d[1], 40)
pde_1d = PDE(domain_1d, real_solution_1d)
#source_term_1d = pde_1d.compute_source_term(grid_points_1d, real_solution_1d)
#nn_source_term_1d = pde_1d.compute_source_term(grid_points_1d, model_nn)
#atest = source_term_1d.reshape(-1,1)-nn_source_term_1d
#print(atest)

# Example usage for 2D:
#domain_2d = (0, 1, 0, 1)
#x_grid = np.linspace(0, 1, 14)
#y_grid = np.linspace(0, 1, 14)
#X,Y = np.meshgrid(x_grid,y_grid)
#pde_2d = PDE(domain_2d, real_solution_2d)


#source_term_2d = pde_2d.compute_source_term((x_grid, y_grid), real_solution_2d)
#print( source_term_2d)



def loss_solve_pde(model,input_data,real_solution=real_solution_1d,regularization = False, lambdak = 0.1):
    
    sample_num = input_data.shape[0]
    pde_1d = PDE((0,1),real_solution_1d)
    grid_points_1d = torch.linspace(0, 1, sample_num, dtype=torch.float32).reshape(-1, 1)
    inner_sample = sample_num-2
    source_term_1d = pde_1d.compute_source_term(grid_points_1d,real_solution_1d).reshape(-1,1)
    def model_NN(input_data,Model = model):
        x = torch.tensor(input_data, dtype=torch.float32).reshape(-1,1)
        return Model(x).detach().numpy()
    model_input = torch.tensor(input_data, dtype=torch.float32).reshape(-1, 1)
    model_output = model(model_input) 
    NN_source_term_1d = pde_1d.compute_source_term(grid_points_1d, lambda x: model(x)).reshape(-1, 1)
    #NN_source_term_1d = pde_1d.compute_source_term(grid_points_1d,model_NN)
    main_cost = (source_term_1d-NN_source_term_1d)[1:-1]
    if regularization == True:
        real_0 = real_solution_1d(input_data[0]).reshape(-1,1)
        real_end = real_solution_1d(input_data[-1])
        nn_0 = model_nn(input_data[0])
        nn_end = model_nn(input_data[-1])
        regularization_term = np.linalg.norm(real_0-nn_0)**2+np.linalg.norm(real_end-nn_end)**2
        regularization_term = lambdak*0.5*0.5*regularization_term
    else:
        regularization_term = 0
    
    return 0.5*np.linalg.norm(main_cost)**2/inner_sample +regularization_term


#Test loss_solve_pde

#NN_source_term_1d = pde_1d.compute_source_term(grid_points_1d,model_NN)
#print(loss_solve_pde(My_model, np.linspace(0,1,40),regularization=True))

def compute_loss(input_data, model, pde, real_solution, lambdak=0.1, regularization=False):
    sample_num = input_data.shape[0]
    grid_points = torch.linspace(0, 1, sample_num, dtype=torch.float32).reshape(-1, 1)
    inner_sample = sample_num - 2
    
    # Compute source term for the real solution (torch tensor)
    source_term = pde.compute_source_term(grid_points, real_solution).reshape(-1, 1)
    
    # Compute model prediction (torch tensor)
    model_input = torch.tensor(input_data, dtype=torch.float32).reshape(-1, 1)
    model_output = model(model_input)
    
    # Compute the source term from the model output (torch tensor)
    NN_source_term = pde.compute_source_term(grid_points, lambda x: model(x)).reshape(-1, 1)
    
    # Compute main cost (torch tensor)
    main_cost = (source_term - NN_source_term)[1:-1]
    main_cost_loss = 0.5 * torch.norm(main_cost)**2 / inner_sample
    
    # Compute regularization term if needed (torch tensor)
    if regularization==True:
        real_0 = real_solution(input_data[0])
        real_end = real_solution(input_data[-1])
        nn_0 = model(model_input[0].reshape(1, -1))
        nn_end = model(model_input[-1].reshape(1, -1))
        
        regularization_term = (torch.norm(real_0 - nn_0)**2 + torch.norm(real_end - nn_end)**2)
        regularization_term = lambdak * 0.5 * regularization_term
    else:
        regularization_term = torch.tensor(0.0)
    
    # Total loss (torch tensor)
    total_loss = main_cost_loss + regularization_term
    
    return total_loss
    
    
def Fk(input_data, model, pde, real_solution):
    sample_num = input_data.shape[0]
    grid_points = torch.linspace(0, 1, sample_num, dtype=torch.float32, requires_grad=True).reshape(-1, 1)
    
    # Compute source term for the real solution (torch tensor)
    source_term = pde.compute_source_term(grid_points, real_solution).reshape(-1, 1)
    
    # Compute model prediction (torch tensor)
    model_input = torch.tensor(input_data, dtype=torch.float32, requires_grad=True).reshape(-1, 1)
    #model_output = model(model_input)
    
    # Compute the source term from the model output (torch tensor)
    NN_source_term = pde.compute_source_term(grid_points, lambda x: model(x)).reshape(-1, 1)
    
    # Compute main cost (torch tensor)
    main_cost = (source_term - NN_source_term)[1:-1]
    
    return main_cost
#PDE_Nontensor
def Jk(input_data, model, pde, real_solution):
    # Compute Fk
    main_cost = Fk(input_data, model, pde, real_solution)
    
    # Ensure requires_grad is True for model parameters
    for param in model.parameters():
        param.requires_grad = True
    
    # Initialize an empty list to store the gradients (Jacobian rows)
    jacobian = []
    
    # Compute the Jacobian matrix
    for i in range(main_cost.size(0)):
        # Zero the gradients
        model.zero_grad()
        
        # Compute the gradient of the i-th component of Fk w.r.t. model parameters
        grad_i = autograd.grad(main_cost[i], model.parameters(), retain_graph=True, create_graph=True)
        
        # Flatten and concatenate the gradients into a single vector
        jacobian_row = torch.cat([g.view(-1) for g in grad_i])
        
        # Append the row to the Jacobian matrix
        jacobian.append(jacobian_row)
    
    # Stack the list of Jacobian rows into a matrix
    jacobian = torch.stack(jacobian)
    
    return jacobian

# Example usage:
# Assuming you have a PDE class and a real_solution_1d function



# Define input data
input_data = torch.linspace(0, 1, 40)

# Define your PDE and real solution functions
class PDE_Nontensor:
    def __init__(self, domain, real_solution):
        self.domain = domain
        self.real_solution = real_solution

    def compute_source_term(self, grid_points, solution_func):
        # Example implementation (should be adapted to your PDE)
        return solution_func(grid_points)



pde = PDE_Nontensor((0,1), real_solution_1d)

# Compute the Jacobian matrix
#loss_main = Fk(input_data, model, pde, real_solution_1d)
#jacobian_matrix = Jk(input_data, model, pde, real_solution_1d)
#print(0.5*(torch.randn(301).T @ jacobian_matrix.T @ jacobian_matrix @torch.randn(301)))
    

#Initialise the parameters of nn
def initialize_parameters(input_dim,r,init_type = 'he'):
    np.random.seed(1234)
    if init_type == 'he':
        w1 = np.random.randn(r,input_dim)*np.sqrt(2./input_dim)
        b1 = np.zeros((r,1))
        w2 = np.random.randn(1,r)*np.sqrt(2./r)
        b2 = np.zeros((1,1))
    elif init_type == 'xvaier':
        w1 = np.random.randn(r, input_dim) * np.sqrt(1. / input_dim)
        b1 = np.zeros((r, 1))
        w2 = np.random.randn(1, r) * np.sqrt(1. / r)
        b2 = np.zeros((1, 1))
    elif init_type == 'random':
       # Random initialization
       w1 = np.random.randn(r, input_dim) * 0.01
       b1 = np.zeros((r, 1))
       w2 = np.random.randn(1, r) * 0.01
       b2 = np.zeros((1, 1))
    else:
       raise ValueError("Unknown initialization type. Use 'he', 'xavier', or 'random'.")

    parameters = {
        'w1': w1,
        'b1': b1.reshape(-1),
        'w2': w2,
        'b2': b2.reshape(-1)
    }

    return parameters

#Test for Initialize
#params_tt = initialize_parameters(1, 2)
#w1_tt = params_tt['w1']
#b1_tt = params_tt['b1']
#w2_tt = params_tt['w2']
#b2_tt = params_tt['b2']
#with torch.no_grad():
    # Set weights and biases for the first hidden layer
#    My_model.hidden_layers[0].weight = nn.Parameter(torch.tensor(w1_tt, dtype=torch.float32))
#    My_model.hidden_layers[0].bias = nn.Parameter(torch.tensor(b1_tt, dtype=torch.float32))

    # Set weights and biases for the remaining hidden layers
    #for i in range(1, n_hidden_layers):
    #    My_model.hidden_layers[i].weight = nn.Parameter(torch.tensor(fixed_weights[i], dtype=torch.float32))
    #    My_model.hidden_layers[i].bias = nn.Parameter(torch.tensor(fixed_biases[i], dtype=torch.float32))

    # Set weights and biases for the output layer
#    My_model.output_layer.weight = nn.Parameter(torch.tensor(w2_tt, dtype=torch.float32))
#    My_model.output_layer.bias = nn.Parameter(torch.tensor(b2_tt, dtype=torch.float32))
    
#print(My_model(input_data))
def compute_jacobian_and_hessian(model, x):
    x = x.reshape(-1, 1)  # Ensure x is a column vector
    x.requires_grad_(True)  # Enable gradient computation

    # Forward pass
    output = model(x)
    
    # Compute Jacobian
    jacobian = autograd.functional.jacobian(lambda x: model(x), x)
    jacobian = torch.diagonal(jacobian.squeeze())
    # Compute Hessian
    def jacobian_f(x):
        jacobian = autograd.functional.jacobian(lambda x: model(x), x)
        jaco = jacobian[jacobian != 0].flatten()
        return jaco
    
    # Ensure output_fn returns a scalar for Hessian calculation
    hessian = autograd.functional.jacobian(jacobian_f, x)
    hessian = torch.diagonal(hessian.squeeze())
    return jacobian, hessian

# Define input tensor
#x = torch.linspace(0, 1, 40, dtype=torch.float32)

# Compute Jacobian and Hessian
#jaco,hess= compute_jacobian_and_hessian(My_model, x)
#print(jaco)
#print(hess)



def model_function(params,x):
    """
        

    Parameters
    ----------
    params : List
    parameters = {
        'w1': w1,
        'b1': b1,
        'w2': w2,
        'b2': b2
       }
        
    """
    x = torch.tensor(x, dtype=torch.float32).reshape(-1,1)
    model_use =  FullyConnectedNN(input_dim,n_hidden_layers , r_nodes_per_layer, output_dim)
    w1 = params['w1']
    b1 = params['b1']
    w2 = params['w2']
    b2 = params['b2']
    with torch.no_grad():
        model_use.hidden_layers[0].weight = nn.Parameter(torch.tensor(w1, dtype=torch.float32))
        model_use.hidden_layers[0].bias = nn.Parameter(torch.tensor(b1, dtype=torch.float32))

        # Set weights and biases for the output layer
        model_use.output_layer.weight = nn.Parameter(torch.tensor(w2, dtype=torch.float32))
        model_use.output_layer.bias = nn.Parameter(torch.tensor(b2, dtype=torch.float32))
    return model_use(x).detach().numpy()





   
def compute_nxx(params,x):
    x = x.reshape(-1,1)
    nn_out = model_function(params, x)
    Nx = jacobian(lambda x: model_function(params,x))(x)
    Nxx = hessian(lambda x: model_function(params,x))(x)
    return Nxx.flatten()
#Taylor expansion
def taylor_loss(s,input_data, model, pde, real_solution, lambda0=0.05, regularization=False):
    #s = torch.randn(3*r_nodes_per_layer+1)
    input_data_tensor = torch.tensor(input_data)
    zero_term = compute_loss(input_data, model, pde, real_solution,regularization=False)
    F_k = Fk(input_data_tensor, model, pde, real_solution_1d)
    J_k = Jk(input_data_tensor, model, pde, real_solution_1d)
    first_term = F_k.T@J_k@s
    B_k = J_k.T@J_k
    second_term = 0.5*(s.T @ B_k @ s)
    if regularization == True:
        re_term = 0.5*lambda0*torch.norm(s)**2
    else:
        re_term = 0
    return zero_term+first_term+second_term+re_term

#Subsolver
def line_A(input_data, model, pde, real_solution, lambda0):
    input_data_tensor = torch.tensor(input_data)
    #F_k = Fk(input_data_tensor, model, PDE((0,1), real_solution_1d), real_solution_1d)
    J_k = Jk(input_data_tensor, model, pde, real_solution_1d)
    B_k = J_k.T@J_k
    shape_eye = B_k.shape[0]
    return B_k+lambda0*torch.eye(shape_eye)


def line_b(input_data, model, pde, real_solution, lambda0):
    input_data_tensor = torch.tensor(input_data)
    F_k = Fk(input_data_tensor, model, pde, real_solution_1d)
    J_k = Jk(input_data_tensor, model, pde, real_solution_1d)
    return -1*J_k.T @F_k


def LMTR(input_data, model, pde, real_solution, lambdak=0.1, regularization=False):
    #input_data = torch.tensor(input_data)
    input_dim = model.hidden_layers[0].in_features
    #n_hidden_layers = 1
    r_nodes_per_layer = model.hidden_layers[0].out_features
    #output_dim = 1
    #activation_function = torch.sigmoid
    #Set up the neural network
    #Model = FullyConnectedNN(input_dim, n_hidden_layers, r_nodes_per_layer, output_dim, activation_function)
    #Initialize the neural network
    #model_param_init = initialize_parameters(input_dim, r_nodes_per_layer)
    w10 = model.hidden_layers[0].weight.data.numpy()
    b10 = model.hidden_layers[0].bias.data.numpy()
    w20 = model.output_layer.weight.data.numpy()
    b20 = model.output_layer.bias.data.numpy()
    #model_param_init = initialize_parameters(input_dim, r_nodes_per_layer)
    #w10 = model_param_init['w1']
    #b10 = model_param_init['b1']
    #w20 = model_param_init['w2']
    #b20 = model_param_init['b2']
    
    
    #model_NN = model_nn(input_data,model = Model)
    
    #Loss = compute_loss(input_data, model, pde, real_solution,lambdak,True)
    ###Optional parameters
    eta1 = 0.1
    eta2 = 0.75
    gamma1 = 0.85
    gamma2 = 0.5
    gamma3 = 1.5
    lambda0 = 0.05
    lambda_min = 10**(-4)
    epsilon = 10**(-4)
    max_iter = 1000
    k = 0
    #Get the gradient
    
    input_data_tensor = torch.tensor(input_data)
    #model_tt = FullyConnectedNN(input_dim, n_hidden_layers, r_nodes_per_layer, output_dim)
    loss = compute_loss(input_data_tensor, model, pde, real_solution, lambdak, regularization=True)

    # Compute gradients
    model.zero_grad()
    loss.backward()  # This should now work since loss is a PyTorch tensor

    # Access gradients
    gradients = torch.cat([param.grad.view(-1) for param in model.parameters()])
    w10_1d = torch.tensor(w10.squeeze())
    w20_1d = torch.tensor(w20.squeeze())
    b10 = torch.tensor(b10)
    b20 = torch.tensor(b20)
    allparams = torch.cat([w10_1d,b10,w20_1d,b20])
    while k<=max_iter and np.linalg.norm(gradients)>=epsilon:
        #print(np.linalg.norm(gradients))
        A_sub = line_A(input_data, model, pde, real_solution, lambda0)
        b_sub = line_b(input_data, model, pde, real_solution, lambda0)
        A_np = A_sub.detach().numpy()
        b_np = b_sub.detach().numpy()

        s_np, info = cg(A_np,b_np)
        s = torch.from_numpy(s_np)
        #print(s)
        
        pred = taylor_loss(torch.zeros_like(b_sub), input_data, model, pde, real_solution,lambda0,regularization=True)-taylor_loss(s, input_data, model, pde, real_solution,lambda0,regularization=True)
        fk = compute_loss(input_data, model, pde, real_solution, lambdak, regularization=True)
        new_params = allparams+s
        w10_new = new_params[:r_nodes_per_layer].view((r_nodes_per_layer,1))
        b10_new = new_params[r_nodes_per_layer:2*r_nodes_per_layer]
        w20_new = new_params[2*r_nodes_per_layer:3*r_nodes_per_layer].view((1,r_nodes_per_layer))
        b20_new = new_params[-1]
        model_new = model
        with torch.no_grad():
            # Set weights and biases for the first hidden layer
            model_new.hidden_layers[0].weight = nn.Parameter(torch.tensor(w10_new, dtype=torch.float32))
            model_new.hidden_layers[0].bias = nn.Parameter(torch.tensor(b10_new, dtype=torch.float32))

            # Set weights and biases for the output layer
            model_new.output_layer.weight = nn.Parameter(torch.tensor(w20_new, dtype=torch.float32))
            model_new.output_layer.bias = nn.Parameter(torch.tensor(b20_new, dtype=torch.float32))
        
        #model_NN = model_nn(input_data,model = model)
        fks = compute_loss(input_data, model_new, pde, real_solution, lambdak, regularization=True)
        ared = fk-fks
        #print(pred)
        pho = ared/pred
        print(pho)
        if pred == 0:
            break
        elif pho >= eta1:
            w10 = w10_new
            b10 = b10_new
            w20 = w20_new
            b20 = b20_new
            #model = model_new
            if pho>=eta2:
                lambda0 = max(lambda_min,gamma2*lambda0)
            else:
                lambda0 = max(lambda_min,gamma1*lambda0)
        else:
            w10 = w10
            b10 = b10
            w20 = w20
            b20 = b20
            #model = model
            lambda0 = gamma3*lambda0
        
        
        with torch.no_grad():
            # Set weights and biases for the first hidden layer
            model_new.hidden_layers[0].weight = nn.Parameter(torch.tensor(w10, dtype=torch.float32))
            model_new.hidden_layers[0].bias = nn.Parameter(torch.tensor(b10, dtype=torch.float32))

            # Set weights and biases for the output layer
            model_new.output_layer.weight = nn.Parameter(torch.tensor(w20, dtype=torch.float32))
            model_new.output_layer.bias = nn.Parameter(torch.tensor(b20, dtype=torch.float32))
        model = model_new
        loss = compute_loss(input_data_tensor, model, pde, real_solution, lambdak, regularization=True)

        # Compute gradients
        model.zero_grad()
        loss.backward()  # This should now work since loss is a PyTorch tensor

        # Access gradients
        gradients = torch.cat([param.grad.view(-1) for param in model.parameters()])
    
        k += 1
        
    input_data = torch.tensor(input_data.reshape(sample_num,input_dim), dtype=torch.float32)
            
    return model(input_data)
            
        
#Test for LMTR
input_dim = 1
n_hidden_layers = 1
r_nodes_per_layer = 100
output_dim = 1
activation_function = torch.tanh
model = FullyConnectedNN(input_dim, n_hidden_layers, r_nodes_per_layer, output_dim, activation_function)
initial_params = initialize_parameters(input_dim,r_nodes_per_layer)
init_w1 = initial_params['w1']
init_b1 = initial_params['b1']
init_w2 = initial_params['w2']
init_b2 = initial_params['b2']
with torch.no_grad():
    model.hidden_layers[0].weight = nn.Parameter(torch.tensor(init_w1, dtype=torch.float32))
    model.hidden_layers[0].bias = nn.Parameter(torch.tensor(init_b1, dtype=torch.float32))

        # Set weights and biases for the output layer
    model.output_layer.weight = nn.Parameter(torch.tensor(init_w2, dtype=torch.float32))
    model.output_layer.bias = nn.Parameter(torch.tensor(init_b2, dtype=torch.float32))

#print(model(torch.tensor(input_data.reshape(40,1), dtype=torch.float32)))

#print(real_solution_1d(input_data))
print(LMTR(input_data, model, pde, real_solution_1d, lambdak=0.1, regularization=True))

#print(compute_loss(input_data, model, pde, real_solution_1d)) 
#print(loss_solve_pde(model, input_data))
