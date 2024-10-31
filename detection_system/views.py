from django.shortcuts import render, redirect, get_object_or_404
from django.core.files.base import ContentFile
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.conf import settings
import numpy as np
import requests
import base64
from PIL import Image
import io
from .models import User, DiseaseDetection
from .forms import MyUserCreationForm, UserProfileForm





# Define a mapping for diseases to their remediation advice
remediation_mapping = {
    "Blackpod": "Remove and destroy infected pods. Improve drainage and avoid overhead irrigation.",
    "OtherDisease": "Follow standard pest management practices.",
    
}



# Define a mapping for the class labels
# Adjust the indices according to your model's output classes
class_mapping = {
    0: 'Diseased',   # Assuming 0 corresponds to Healthy
    1: 'Healthy',  # Assuming 1 corresponds to Diseased
    # Add more mappings if your model predicts more classes
}

def compress_image(image, max_size_kb=500, quality=85):
    if image.mode == 'RGBA':
        image = image.convert('RGB')  # Convert RGBA to RGB

    img_io = io.BytesIO()  # In-memory file
    image.save(img_io, format='JPEG', quality=quality)
    img_size_kb = img_io.tell() / 1024

    while img_size_kb > max_size_kb and quality > 10:
        img_io = io.BytesIO()
        quality -= 10
        image.save(img_io, format='JPEG', quality=quality)
        img_size_kb = img_io.tell() / 1024

    img_io.seek(0)
    compressed_image = Image.open(img_io)
    return compressed_image

def load_and_preprocess_image(image, max_size_kb=500):
    img = Image.open(image)
    img = compress_image(img, max_size_kb=max_size_kb)
    img = img.resize((224, 224))  # Resize for the model
    img_array = np.array(img) / 255.0  # Normalize the image
    return img_array



def home(request):
    return render(request, 'cogurad/index.html')
def about(request):
    return render(request, 'cogurad/about.html')
def registerPage(request):
    form = MyUserCreationForm()  # Initialize the form
    if request.method == 'POST':
        form = MyUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.username = user.username.lower()
            user.save()
            login(request, user)
            return redirect('dashboard')
        else:
            # Show error messages only if the form is invalid
            for error in form.errors.values():
                messages.error(request, ' '.join(error))
    
    return render(request, 'cogurad/login_register.html', {'form': form})

def loginPage(request):
    page = 'login'
    if request.user.is_authenticated:
        return redirect('dashboard')
    if request.method == 'POST':
        email = request.POST.get('email').lower()
        password = request.POST.get('password')
        try:
            user = User.objects.get(email=email)
        except:
            messages.error(request, 'User does not exist')
        user = authenticate(request, email=email, password=password)

        if user is not None:
            login(request, user)
            return redirect('dashboard')
        else:
            messages.error(request, 'Username **OR password does not exit')

    context = {'page': page}
    return render(request, 'cogurad/login_register.html', context)

def logoutUser(request):
    logout(request)
    return redirect('home')

@login_required
def dashboard(request):
    user = None
    try:
        user = User.objects.get(id=request.user.id)
        detections = DiseaseDetection.objects.filter(user=user).order_by('-date')  
        
        total_images_uploaded = detections.count()  
        total_disease_predictions = detections.filter(disease__isnull=False).count()  

        
        if total_images_uploaded > 0:
            prediction_accuracy = (total_disease_predictions / total_images_uploaded) * 100
        else:
            prediction_accuracy = 0 

    except User.DoesNotExist:
        messages.error(request, 'User does not exist')
    if user:
        context = {
            'detections': detections,
            'total_images_uploaded': total_images_uploaded,
            'total_disease_predictions': total_disease_predictions,
            'prediction_accuracy': prediction_accuracy,
        }        
        return render(request, 'cogurad/dashboard.html',context)
    else:
        return redirect('login')
@login_required
def camera(request):
    user = None
    try:
        user = User.objects.get(id=request.user.id)
    except User.DoesNotExist:
        messages.error(request, 'User does not exist')
    if user:        
        return render(request, 'cogurad/camera.html')
    else:
        return redirect('login')
@login_required
def upload(request):
    user = None
    try:
        user = User.objects.get(id=request.user.id)
    except User.DoesNotExist:
        messages.error(request, 'User does not exist')
    if user:        
        return render(request, 'cogurad/upload.html')
    else:
        return redirect('login')


@login_required
def profile(request, pk):
    user = get_object_or_404(User, id=pk)

    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES, instance=user)
        
        if form.is_valid():            
            form.save()           
            old_password = request.POST.get('old_password')
            new_password = request.POST.get('new_password')

            if old_password and new_password:
                if check_password(old_password, user.password):
                    user.set_password(new_password)  
                    user.save()  
                    update_session_auth_hash(request, user)  
                else:
                    print("Old password is incorrect")  
                
            return redirect('profile', pk=user.id)  
        else:
            print(form.errors)  
    else:
        form = UserProfileForm(instance=user)

    return render(request, 'cogurad/profile.html', {'user': user, 'form': form})


@login_required
def analytics(request):
    user = None
    try:
        user = User.objects.get(id=request.user.id)
        detections = DiseaseDetection.objects.filter(user=user).order_by('-date')  # Fetch the user's detections
        
        total_images_uploaded = detections.count()  # Count total images uploaded
        total_disease_predictions = detections.filter(disease__isnull=False).count()  # Count total disease predictions

        # Assuming you want to calculate prediction accuracy
        if total_images_uploaded > 0:
            # For example, you could have a field in your model to track the total predictions 
            # Here, we will just assume that all predictions are valid since we're counting all detections
            prediction_accuracy = (total_disease_predictions / total_images_uploaded) * 100
        else:
            prediction_accuracy = 0  # Avoid division by zero

        context = {
            'detections': detections,
            'total_images_uploaded': total_images_uploaded,
            'total_disease_predictions': total_disease_predictions,
            'prediction_accuracy': prediction_accuracy,
        }   
    except User.DoesNotExist:
        messages.error(request, 'User does not exist')
    
    if user:        
        return render(request, 'cogurad/analytics.html', context)
    else:
        return redirect('login')
@login_required
def support(request):
    user = None
    try:
        user = User.objects.get(id=request.user.id)
    except User.DoesNotExist:
        messages.error(request, 'User does not exist')
    if user:        
        return render(request, 'cogurad/support.html')
    else:
        return redirect('login')



@login_required
def predict(request):
    if request.method == 'POST':
        # Handle image input, either from file upload or camera capture
        if 'image' in request.FILES:
            uploaded_file = request.FILES['image']
        elif 'capturedImage' in request.POST:
            image_data = request.POST['capturedImage']
            header, encoded = image_data.split(',', 1)
            binary_data = base64.b64decode(encoded)
            uploaded_file = ContentFile(binary_data, name='capturedImage.png')
        else:
            return render(request, 'cogurad/result.html', {'error': 'No image uploaded.'})

        # Save the uploaded file to the DiseaseDetection model's image field
        disease_detection = DiseaseDetection(user=request.user, image=uploaded_file)
        disease_detection.save()

        # Load, compress, and preprocess the image
        image_path = disease_detection.image.path
        preprocessed_image = load_and_preprocess_image(image_path)

        # Convert the preprocessed image back to an in-memory file for the API request
        img_io = io.BytesIO()
        compressed_image = Image.fromarray((preprocessed_image * 255).astype('uint8'))
        compressed_image.save(img_io, format='JPEG')
        img_io.seek(0)  # Reset file pointer to the beginning

        # Prepare the compressed image for the request to the Flask API
        files = {'file': ('compressed_image.jpg', img_io, 'image/jpeg')}
        try:
            # Send the request to the Flask API
            response = requests.post('http://51.20.115.169/predict', files=files)
            response_data = response.json()

            if response.status_code == 200:
                # Parse the response data
                predicted_class = response_data.get("predicted_class", "Unknown").lower()
                confidence_scores = response_data.get("confidence_scores", {})

                # If the predicted class is not "healthy", set it as "Diseased"
                if predicted_class != "healthy":
                    predicted_class = "Diseased"
                    remediation_message = "Remove and destroy infected pods. Improve drainage and avoid overhead irrigation."
                else:
                    remediation_message = "No remediation needed."

                # Update the DiseaseDetection object with the results
                disease_detection.disease = predicted_class.capitalize()
                disease_detection.remediation = remediation_message
                disease_detection.save()
    
                # Render results in the template
                return render(request, 'cogurad/result.html', {
                    'predicted_class': predicted_class.capitalize(),
                    'confidence_scores': confidence_scores,
                    'file_url': disease_detection.image.url
                })
            else:
                return render(request, 'cogurad/result.html', {'error': 'Prediction failed.'})
        except requests.exceptions.RequestException as e:
            return render(request, 'cogurad/result.html', {'error': f"Request to prediction API failed: {e}"})
