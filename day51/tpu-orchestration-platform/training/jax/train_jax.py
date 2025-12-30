"""
JAX TPU Training Pipeline
Demonstrates TPU-optimized training with JAX
"""
import jax
import jax.numpy as jnp
from jax import random, grad, jit, vmap, pmap
import time

print("JAX TPU Training Pipeline")
print(f"JAX version: {jax.__version__}")
print(f"Devices: {jax.devices()}")

# Simple model for demonstration
def simple_model(params, x):
    """Simple dense network"""
    w1, b1, w2, b2 = params
    hidden = jnp.tanh(jnp.dot(x, w1) + b1)
    output = jnp.dot(hidden, w2) + b2
    return output

def loss_fn(params, batch):
    """Compute loss"""
    x, y = batch
    predictions = simple_model(params, x)
    return jnp.mean((predictions - y) ** 2)

@jit
def train_step(params, batch, learning_rate=0.01):
    """Single training step (JIT compiled for TPU)"""
    loss, grads = jax.value_and_grad(loss_fn)(params, batch)
    
    # Update parameters
    params = [
        p - learning_rate * g 
        for p, g in zip(params, grads)
    ]
    
    return params, loss

# Initialize parameters
key = random.PRNGKey(0)
input_size, hidden_size, output_size = 128, 256, 10

w1 = random.normal(key, (input_size, hidden_size)) * 0.01
b1 = jnp.zeros((hidden_size,))
w2 = random.normal(key, (hidden_size, output_size)) * 0.01
b2 = jnp.zeros((output_size,))

params = [w1, b1, w2, b2]

# Training loop
print("\nStarting training...")
num_steps = 100
batch_size = 128

for step in range(num_steps):
    # Generate random batch
    key, subkey = random.split(key)
    x = random.normal(subkey, (batch_size, input_size))
    y = random.normal(subkey, (batch_size, output_size))
    
    batch = (x, y)
    
    # Train step
    start = time.time()
    params, loss = train_step(params, batch)
    step_time = (time.time() - start) * 1000
    
    if step % 10 == 0:
        print(f"Step {step}: loss={loss:.4f}, time={step_time:.2f}ms")

print("\n✓ JAX training completed successfully")
print(f"Final loss: {loss:.4f}")
