import torch
from efficientnet_pytorch import EfficientNet
import torchvision.transforms as transforms
from PIL import Image

class BlindnessModel:
    def __init__(self, model_path=None):
        self.model = EfficientNet.from_name('efficientnet-b0', num_classes=5)  # 5 DR stages
        if model_path:
            self.model.load_state_dict(torch.load(model_path, map_location='cpu'))
        self.model.eval()

        self.transform = transforms.Compose([
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize([0.485, 0.456, 0.406], 
                                 [0.229, 0.224, 0.225])
        ])
        self.labels = ['No DR', 'Mild', 'Moderate', 'Severe', 'Blind']

    def predict(self, image: Image.Image):
        image = self.transform(image).unsqueeze(0)  # Batch of 1
        with torch.no_grad():
            outputs = self.model(image)
            probs = torch.softmax(outputs, dim=1).squeeze()
            predicted_class = torch.argmax(probs).item()
        return self.labels[predicted_class], probs[predicted_class].item()
