import os
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import torch
from torchvision import transforms, datasets
from torch.utils.data import DataLoader
import torch.nn as nn
import torch.nn.functional as F
import torch.optim as optim

# Define the custom edge detection transform
class EdgeDetectionTransform:
    def __call__(self, img):
        img = np.array(img)
        if len(img.shape) == 3:  # Convert color image to grayscale
            img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        edges = cv2.Canny(img, 100, 200)
        return Image.fromarray(edges)

# Data augmentation pipeline
data_transforms = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.RandomHorizontalFlip(),
    EdgeDetectionTransform(),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.5], std=[0.5])
])

# Specify the path to your dataset here
dataset_path = 'C:\\Users\\KIIT\\Desktop\\Project\\Task1\\Faces\\Data'  # Replace this with the actual path

# Create the dataset and dataloader
train_dataset = datasets.ImageFolder(root=dataset_path, transform=data_transforms)
train_loader = DataLoader(train_dataset, batch_size=32, shuffle=True)

# Define the simple CNN model
class SimpleCNN(nn.Module):
    def __init__(self):
        super(SimpleCNN, self).__init__()
        self.conv1 = nn.Conv2d(1, 32, kernel_size=3, stride=1, padding=1)
        self.conv2 = nn.Conv2d(32, 64, kernel_size=3, stride=1, padding=1)
        self.fc1 = nn.Linear(64 * 56 * 56, 128)
        self.fc2 = nn.Linear(128, 2)  # Assuming 2 classes (real and spoof)

    def forward(self, x):
        x = F.relu(self.conv1(x))
        x = F.max_pool2d(x, 2)
        x = F.relu(self.conv2(x))
        x = F.max_pool2d(x, 2)
        x = x.view(-1, 64 * 56 * 56)
        x = F.relu(self.fc1(x))
        x = self.fc2(x)
        return x

# Initialize the model, loss function, and optimizer
model = SimpleCNN()
criterion = nn.CrossEntropyLoss()
optimizer = optim.Adam(model.parameters(), lr=0.001)

# Training loop
num_epochs = 10
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
model.to(device)

for epoch in range(num_epochs):
    model.train()
    running_loss = 0.0
    for inputs, labels in train_loader:
        inputs, labels = inputs.to(device), labels.to(device)
        
        optimizer.zero_grad()
        outputs = model(inputs)
        loss = criterion(outputs, labels)
        loss.backward()
        optimizer.step()
        
        running_loss += loss.item()
    
    print(f"Epoch {epoch + 1}/{num_epochs}, Loss: {running_loss / len(train_loader)}")

# Define the path where you want to save the model
save_dir = 'path/to/save/directory'  # Replace with your desired directory
os.makedirs(save_dir, exist_ok=True)  # Create the directory if it doesn't exist
model_path = os.path.join(save_dir, 'model.pth')

# Save the trained model
torch.save(model.state_dict(), model_path)

# Define the data transformations
data_transforms = transforms.Compose([
    transforms.Resize((224, 224)),
    EdgeDetectionTransform(),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.5], std=[0.5])
])

def predict_image(image_path, model, device):
    model.eval()  # Set the model to evaluation mode
    image = Image.open(image_path).convert('RGB')  # Open the image and convert it to RGB
    image_transformed = data_transforms(image).unsqueeze(0).to(device)  # Apply transformations and add batch dimension
    
    with torch.no_grad():  # Disable gradient computation
        outputs = model(image_transformed)  # Get model outputs
        _, predicted = torch.max(outputs, 1)  # Get the class with the highest score
    
    return 'real' if predicted.item() == 0 else 'spoof'  # Map prediction to class name

def annotate_and_save(image_path, prediction, output_dir):
    image = Image.open(image_path)
    draw = ImageDraw.Draw(image)
    font = ImageFont.load_default()
    text = f"Prediction: {prediction}"
    draw.text((10, 10), text, font=font, fill=(255, 0, 0))  # Draw text on image
    os.makedirs(output_dir, exist_ok=True)
    base_name = os.path.basename(image_path)
    save_path = os.path.join(output_dir, base_name)
    image.save(save_path)

# Load the model from the saved file
model = SimpleCNN()
model.load_state_dict(torch.load(model_path))
model.to(device)

# Predict and annotate images in a folder
input_folder = 'C:\\Users\\KIIT\\Desktop\\Project\\Task1\\Faces\\Spoof_Sample'  # Replace with the path to your folder of images
output_folder = 'C:\\Users\\KIIT\\Desktop\\Project\\Task1\\ModelTraining\\Results4'  # Replace with the path to save annotated images

for img_name in os.listdir(input_folder):
    if img_name.endswith(('.jpg', '.jpeg', '.png')):
        img_path = os.path.join(input_folder, img_name)
        prediction = predict_image(img_path, model, device)
        annotate_and_save(img_path, prediction, output_folder)

print("Predictions and annotations completed.")