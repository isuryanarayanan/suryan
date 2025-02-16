from flask import Flask, jsonify
from pybars import Compiler

app = Flask(__name__)

# Define the template



@app.route('/client_app_trial_activation_success', methods=['GET'])
def client_app_trial_activation_success():
    with open('./templates/client_app_trial_activation_success.html', 'r') as file:
        template = file.read()

    # Define the dynamic variables
    data = {
        "app": {
            # Application details
            "key": "interact-whatsapp",
            "name": "WareIQ Interact : Whatsapp",
            "image": "https://wareiq-apps.s3.amazonaws.com/interact-whatsapp-app-icon.png",
            "description": "Keep your customers updated with their order with WareIQ’s Interact Application.",

            # Subscription details
            "expiry_date": "2025-08-15",
            "activation_date": "2025-02-15",
            "renewal_date": "2025-08-01",
            "limit": 1000,
            "limit_units": "sms",
            "contents": [
                {
                    "image": "https://wareiq-apps.s3.amazonaws.com/appDetails/interact-sms-app-1.png",
                    "paragraphs": [
                        "<b>Why WareIQ SMS?</b><ul><li>Provide reassurance that the order has been successfully placed.</li><li>Help you track your package</li><li>Receive SMS notifications with updates about its status</li></ul>",
                    ],
                },
                {
                    "image": "https://wareiq-apps.s3.amazonaws.com/appDetails/interact-sms-app-2.png",
                    "paragraphs": [
                        "<b>Benefits of WareIQ SMS: </b> <br><ul><li>A convenient way to stay up-to-date on the status</li><li>Receive updates on your order as soon as they happen</li><li>By receiving alerts for every transaction, you can quickly identify any suspicious activity</li><li>This can help improve your overall customer service experience</li></ul>",
                    ],
                },
            ],
        },
        "user": {"name": "suryan"},
        "base_url": "https://webapp.wareiq.com"
    }
    
    compiler = Compiler()
    template = compiler.compile(template)
    rendered_email = template(data)

    return rendered_email 

@app.route('/client_app_activation_success', methods=['GET'])
def client_app_activation_success():
    template = """"""
    data = {
        "app": {
            "name": "Weight Freeze",
            "image": "https://example.com/app-image.png",
            "description": "This app helps in maintaining stable weight measurements.",
            "activation_date": "2025-02-15",
            "expiry_date": "2025-08-15",
            "renewal_date": "2025-08-01",
            "subscription": {
                "price": 499,
                "name": "Premium Plan",
                "desc": "Access to all features and priority support.",
                "benefits": ["Unlimited usage", "24/7 Support", "Advanced analytics"]
            }
        },
        "user": {"name": "John Doe"}
    }
    
    compiler = Compiler()
    template = compiler.compile(template)
    rendered_email = template(data)

    return rendered_email 

@app.route('/client_app_deactivation_success', methods=['GET'])
def client_app_deactivation_success():
    template = """"""
    data = {
        "app": {
            "name": "Weight Freeze",
            "image": "https://example.com/app-image.png",
            "description": "This app helps in maintaining stable weight measurements.",
            "activation_date": "2025-02-15",
            "expiry_date": "2025-08-15",
            "renewal_date": "2025-08-01",
            "subscription": {
                "price": 499,
                "name": "Premium Plan",
                "desc": "Access to all features and priority support.",
                "benefits": ["Unlimited usage", "24/7 Support", "Advanced analytics"]
            }
        },
        "user": {"name": "John Doe"}
    }
    
    compiler = Compiler()
    template = compiler.compile(template)
    rendered_email = template(data)

    return rendered_email 

@app.route('/client_app_wiq_deactivation_success', methods=['GET'])
def client_app_wiq_deactivation_success():
    template = """"""
    data = {
        "app": {
            "name": "Weight Freeze",
            "image": "https://example.com/app-image.png",
            "description": "This app helps in maintaining stable weight measurements.",
            "activation_date": "2025-02-15",
            "expiry_date": "2025-08-15",
            "renewal_date": "2025-08-01",
            "subscription": {
                "price": 499,
                "name": "Premium Plan",
                "desc": "Access to all features and priority support.",
                "benefits": ["Unlimited usage", "24/7 Support", "Advanced analytics"]
            }
        },
        "user": {"name": "John Doe"}
    }
    
    compiler = Compiler()
    template = compiler.compile(template)
    rendered_email = template(data)

    return rendered_email 
if __name__ == '__main__':
    app.run(debug=True)
