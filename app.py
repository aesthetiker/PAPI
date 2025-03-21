from flask import Flask, render_template, request, redirect, url_for, jsonify
import requests
import json
import logging
import time
from datetime import datetime, timedelta

app = Flask(__name__)

# Configure logging
logging.basicConfig(level=logging.DEBUG)

# OAuth 2.0 Configuration
TOKEN_URL = "https://partner.preprod.flexilis.com/oauth2/token"
PARTNER_CP_KEY = "Replace with your key"

# API Configuration
API_BASE_URL = "https://partner.preprod.flexilis.com"

# Token storage
token_data = {
    "access_token": None,
    "refresh_token": None,
    "expires_at": None
}

def get_access_token():
    global token_data
    current_time = datetime.now()
    
    if token_data["access_token"] and token_data["expires_at"] and current_time < token_data["expires_at"]:
        return token_data["access_token"]
    
    if token_data["refresh_token"]:
        return refresh_access_token()
    
    data = {
        "grant_type": "client_credentials"
    }
    
    headers = {
        "Accept": "application/json",
        "Authorization": f"Bearer {PARTNER_CP_KEY}"
    }
    
    try:
        response = requests.post(TOKEN_URL, data=data, headers=headers)
        response.raise_for_status()
        new_token_data = response.json()
        token_data["access_token"] = new_token_data.get("access_token")
        token_data["refresh_token"] = new_token_data.get("refresh_token")
        token_data["expires_at"] = current_time + timedelta(seconds=new_token_data.get("expires_in", 3600))
        return token_data["access_token"]
    except requests.exceptions.RequestException as e:
        logging.error(f"Error obtaining access token: {str(e)}")
        return None

#This is for fetching the tenants

@app.route('/')
def index():
    access_token = get_access_token()
    if not access_token:
        return render_template('error.html', error_message="Failed to obtain access token")
    
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Accept": "application/json"
    }
    
    try:
        # Fetch tenants
        tenants_response = requests.get(f"{API_BASE_URL}/api/partners/v1/tenants?offset=0&limit=20", headers=headers)
        tenants_response.raise_for_status()
        logging.debug(f"Tenants API Response Content: {tenants_response.content}")
        
        if not tenants_response.content:
            return render_template('error.html', error_message="Empty response from Tenants API")
        
        tenants_data = tenants_response.json()
        tenants = tenants_data.get('tenants', [])
        
        # Create a dictionary to track which tenants are managed
        managed_tenants = {}
        
        # Fetch organizations
        orgs_response = requests.get(f"{API_BASE_URL}/api/partners/v1/orgs", headers=headers)
        orgs_response.raise_for_status()
        
        orgs = []
        if orgs_response.content:
            orgs_data = orgs_response.json()
            orgs = orgs_data.get('orgs', [])
            
            # For each organization, fetch its managed tenants
            for org in orgs:
                org_id = org['externalOrgId']
                org_name = org['name']
                
                # Call the API to get tenants managed by this org
                org_tenants_response = requests.get(
                    f"{API_BASE_URL}/api/partners/v1/orgs/{org_id}/tenants", 
                    headers=headers
                )
                
                if org_tenants_response.status_code == 200 and org_tenants_response.content:
                    org_tenants_data = org_tenants_response.json()
                    org_tenants = org_tenants_data.get('tenants', [])
                    
                    # Mark each tenant as managed by this org
                    for org_tenant in org_tenants:
                        tenant_id = org_tenant['externalPartnerId']
                        managed_tenants[tenant_id] = {
                            'managed': True,
                            'orgId': org_id,
                            'orgName': org_name
                        }
        
        # Enhance tenant data with organization info
        for tenant in tenants:
            tenant_id = tenant['externalPartnerId']
            if tenant_id in managed_tenants:
                tenant['managed'] = True
                tenant['orgId'] = managed_tenants[tenant_id]['orgId']
                tenant['orgName'] = managed_tenants[tenant_id]['orgName']
            else:
                tenant['managed'] = False
                tenant['orgId'] = ''
                tenant['orgName'] = '-'
        
        return render_template('index.html', tenants=tenants, orgs=orgs)
    except requests.exceptions.RequestException as e:
        error_message = f"Error fetching data: {str(e)}"
        if hasattr(e, 'response') and e.response is not None:
            if e.response.status_code == 401:
                error_message = "Authentication failed. Please check your API key."
            elif e.response.status_code == 404:
                error_message = "API endpoint not found. Please check the URL."
        logging.error(error_message)
        return render_template('error.html', error_message=error_message)
    except json.JSONDecodeError as e:
        error_message = f"Invalid JSON response from the API: {str(e)}"
        logging.error(error_message)
        return render_template('error.html', error_message=error_message)

# Tenant Management API routes
@app.route('/api/mgmt/tenants/<tenant_id>/keys', methods=['GET'])
def get_tenant_keys(tenant_id):
    access_token = get_access_token()
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Accept": "application/json"
    }
    
    try:
        response = requests.get(f"{API_BASE_URL}/api/partners/v1/mgmt/tenants/{tenant_id}/application_keys", headers=headers)
        response.raise_for_status()
        return jsonify(response.json()), 200
    except requests.exceptions.RequestException as e:
        app.logger.error(f"Error fetching tenant keys: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/mgmt/tenants/<tenant_id>/keys', methods=['POST'])
def create_tenant_key(tenant_id):
    access_token = get_access_token()
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Accept": "application/json",
        "Content-Type": "application/json"
    }
    
    try:
        data = request.json or {}
        response = requests.post(f"{API_BASE_URL}/api/partners/v1/mgmt/tenants/{tenant_id}/application_keys", headers=headers, json=data)
        response.raise_for_status()
        return jsonify(response.json()), 200
    except requests.exceptions.RequestException as e:
        app.logger.error(f"Error creating tenant key: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/mgmt/tenants/<tenant_id>/keys/<key_guid>', methods=['GET'])
def get_tenant_key(tenant_id, key_guid):
    access_token = get_access_token()
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Accept": "application/json"
    }
    
    try:
        response = requests.get(f"{API_BASE_URL}/api/partners/v1/mgmt/tenants/{tenant_id}/application_keys/{key_guid}", headers=headers)
        response.raise_for_status()
        return jsonify(response.json()), 200
    except requests.exceptions.RequestException as e:
        app.logger.error(f"Error fetching tenant key: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/mgmt/tenants/<tenant_id>/keys/<key_guid>', methods=['DELETE'])
def delete_tenant_key(tenant_id, key_guid):
    access_token = get_access_token()
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Accept": "application/json"
    }
    
    try:
        response = requests.delete(f"{API_BASE_URL}/api/partners/v1/mgmt/tenants/{tenant_id}/application_keys/{key_guid}", headers=headers)
        response.raise_for_status()
        return jsonify(response.json()), 200
    except requests.exceptions.RequestException as e:
        app.logger.error(f"Error deleting tenant key: {str(e)}")
        return jsonify({"error": str(e)}), 500

# Organization Management API routes
@app.route('/api/mgmt/orgs/<org_id>/keys', methods=['GET'])
def get_org_keys(org_id):
    access_token = get_access_token()
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Accept": "application/json"
    }
    
    try:
        response = requests.get(f"{API_BASE_URL}/api/partners/v1/mgmt/orgs/{org_id}/application_keys", headers=headers)
        response.raise_for_status()
        return jsonify(response.json()), 200
    except requests.exceptions.RequestException as e:
        app.logger.error(f"Error fetching organization keys: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/mgmt/orgs/<org_id>/keys', methods=['POST'])
def create_org_key(org_id):
    access_token = get_access_token()
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Accept": "application/json",
        "Content-Type": "application/json"
    }
    
    try:
        data = request.json or {}
        response = requests.post(f"{API_BASE_URL}/api/partners/v1/mgmt/orgs/{org_id}/application_keys", headers=headers, json=data)
        response.raise_for_status()
        return jsonify(response.json()), 200
    except requests.exceptions.RequestException as e:
        app.logger.error(f"Error creating organization key: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/mgmt/orgs/<org_id>/keys/<key_guid>', methods=['GET'])
def get_org_key(org_id, key_guid):
    access_token = get_access_token()
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Accept": "application/json"
    }
    
    try:
        response = requests.get(f"{API_BASE_URL}/api/partners/v1/mgmt/orgs/{org_id}/application_keys/{key_guid}", headers=headers)
        response.raise_for_status()
        return jsonify(response.json()), 200
    except requests.exceptions.RequestException as e:
        app.logger.error(f"Error fetching organization key: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/mgmt/orgs/<org_id>/keys/<key_guid>', methods=['DELETE'])
def delete_org_key(org_id, key_guid):
    access_token = get_access_token()
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Accept": "application/json"
    }
    
    try:
        response = requests.delete(f"{API_BASE_URL}/api/partners/v1/mgmt/orgs/{org_id}/application_keys/{key_guid}", headers=headers)
        response.raise_for_status()
        return jsonify(response.json()), 200
    except requests.exceptions.RequestException as e:
        app.logger.error(f"Error deleting organization key: {str(e)}")
        return jsonify({"error": str(e)}), 500


# Get organization details by ID
# This endpoint retrieves detailed information about a specific organization
@app.route('/api/org/<org_id>', methods=['GET'])
def get_org_details(org_id):
    access_token = get_access_token()
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Accept": "application/json"
    }
    
    try:
        response = requests.get(f"{API_BASE_URL}/api/partners/v1/orgs/{org_id}", headers=headers)
        response.raise_for_status()
        return jsonify(response.json()), 200
    except requests.exceptions.RequestException as e:
        app.logger.error(f"Error fetching organization details: {str(e)}")
        return jsonify({"error": str(e)}), 500

# Update organization default status
# This endpoint allows setting an organization as the default organization
@app.route('/api/org/<org_id>/default', methods=['PUT'])
def update_org_default(org_id):
    access_token = get_access_token()
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Accept": "application/json",
        "Content-Type": "application/json"
    }
    
    try:
        data = request.json
        response = requests.put(f"{API_BASE_URL}/api/partners/v1/orgs/{org_id}/default", headers=headers, json=data)
        response.raise_for_status()
        return jsonify(response.json()), 200
    except requests.exceptions.RequestException as e:
        app.logger.error(f"Error updating organization default status: {str(e)}")
        return jsonify({"error": str(e)}), 500


#This is for for the view button

@app.route('/api/tenant/<tenant_id>', methods=['GET'])
def get_tenant(tenant_id):
    access_token = get_access_token()
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Accept": "application/json"
    }
    
    try:
        # Use the tenant_id parameter from the route
        response = requests.get(f"{API_BASE_URL}/api/partners/v1/tenants/{tenant_id}/data_bundle", headers=headers)
        response.raise_for_status()
        return jsonify(response.json()), 200
    except requests.exceptions.RequestException as e:
        app.logger.error(f"Error fetching tenant details: {str(e)}")
        return jsonify({"error": str(e)}), 500


#This could be for edit

@app.route('/api/orders/modify', methods=['POST'])
def modify_order():
    access_token = get_access_token()
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Accept": "application/json",
        "Content-Type": "application/json"
    }
    
    try:
        # Get the request data
        data = request.json
        
        # Send the modify request to the orders/modify endpoint
        response = requests.post(
            f"{API_BASE_URL}/api/partners/v1/orders/modify", 
            headers=headers, 
            json=data
        )
        response.raise_for_status()
        return jsonify(response.json()), 200
    except requests.exceptions.RequestException as e:
        app.logger.error(f"Error modifying order: {str(e)}")
        return jsonify({"error": str(e)}), 500

#This is for cancel an order

@app.route('/api/orders/cancel', methods=['POST'])
def cancel_order():
    access_token = get_access_token()
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Accept": "application/json",
        "Content-Type": "application/json"
    }
    
    try:
        # Get the request data
        data = request.json
        
        # Send the cancel request to the orders/cancel endpoint
        response = requests.post(
            f"{API_BASE_URL}/api/partners/v1/orders/cancel", 
            headers=headers, 
            json=data
        )
        response.raise_for_status()
        return jsonify(response.json()), 200
    except requests.exceptions.RequestException as e:
        app.logger.error(f"Error cancelling order: {str(e)}")
        return jsonify({"error": str(e)}), 500

#This is for ORG 
@app.route('/api/new_org', methods=['POST'])
def create_new_org():
    access_token = get_access_token()
    if not access_token:
        logging.error("Failed to obtain access token for order creation")
        return jsonify({"error": "Authentication failed"}), 401
    
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Accept": "application/json",
        "Content-Type": "application/json"
    }
    
    try:
        # Check if we have JSON data
        if not request.is_json:
            logging.error(f"Invalid request format. Expected JSON, got: {request.content_type}")
            return jsonify({"error": "Request must be in JSON format"}), 400
        
        data = request.json
        logging.debug(f"Received order data: {data}")
        
        # Validate required fields
        required_fields = ["transactionId", "externalPartnerId", "seatTotal", "defaultOrganization", 
                           "commercialPartnerName", "contactEmail", "contactFirstName", "contactLastName", "name"]
        missing_fields = [field for field in required_fields if field not in data or not data[field]]
        
        if missing_fields:
            logging.error(f"Missing required fields: {missing_fields}")
            return jsonify({"error": f"Missing required fields: {', '.join(missing_fields)}"}), 400
         
        # Make the API request
        print(data)
        response = requests.post(f"{API_BASE_URL}/api/partners/v1/orders", headers=headers, json=data)
        response.raise_for_status()
        
        logging.info(f"Order created successfully: {response.json()}")
        return jsonify(response.json()), 201
    
    except requests.exceptions.HTTPError as e:
        error_message = f"HTTP error creating order: {str(e)}"
        logging.error(error_message)
        
        # Try to extract more detailed error information
        error_detail = "Unknown error"
        if hasattr(e, 'response') and e.response is not None:
            try:
                error_detail = e.response.json()
            except:
                error_detail = e.response.text
                
        return jsonify({"error": error_message, "details": error_detail}), e.response.status_code if hasattr(e, 'response') else 500
    
    except requests.exceptions.RequestException as e:
        error_message = f"Error creating order: {str(e)}"
        logging.error(error_message)
        return jsonify({"error": error_message}), 500
    
    except Exception as e:
        error_message = f"Unexpected error creating order: {str(e)}"
        logging.error(error_message)
        return jsonify({"error": error_message}), 500

# Create a new tenant order
# This endpoint creates a new tenant order with support for both regular and managed tenants
@app.route('/api/new_order', methods=['POST'])
def create_new_order():
    access_token = get_access_token()
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Accept": "application/json",
        "Content-Type": "application/json"
    }
    
    try:
        # Get the request data
        data = request.json
        logging.debug(f"Received order data: {data}")
        
        # Validate required fields
        required_fields = ['transactionId', 'externalPartnerId', 'seatTotal', 'contactEmail', 
                          'contactFirstName', 'contactLastName', 'companyName']
        
        # Add managed-specific required fields
        if data.get('managed', False):
            required_fields.append('externalOrgId')
        
        missing_fields = [field for field in required_fields if not data.get(field)]
        if missing_fields:
            logging.error(f"Missing required fields: {missing_fields}")
            return jsonify({"error": f"Missing required fields", "details": missing_fields}), 400
        
        # Send the order creation request
        response = requests.post(
            f"{API_BASE_URL}/api/partners/v1/orders", 
            headers=headers, 
            json=data
        )
        response.raise_for_status()
        return jsonify(response.json()), 200
    except requests.exceptions.RequestException as e:
        app.logger.error(f"Error creating order: {str(e)}")
        return jsonify({"error": str(e)}), 500


#This is for fetching the orgs
@app.route('/api/orgs', methods=['GET'])
def get_orgs():
    access_token = get_access_token()
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Accept": "application/json"
    }
    
    try:
        response = requests.get(f"{API_BASE_URL}/api/partners/v1/orgs", headers=headers)
        response.raise_for_status()
        orgs_data = response.json()
        orgs = orgs_data.get('orgs', [])
        return jsonify(orgs), 200
    except requests.exceptions.RequestException as e:
        app.logger.error(f"Error fetching organizations: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.errorhandler(Exception)
def handle_exception(e):
    # Log the error
    logging.error(f"Unhandled exception: {str(e)}")
    
    # Return a JSON response for API routes
    if request.path.startswith('/api/'):
        return jsonify({"error": "Internal server error", "message": str(e)}), 500
    
    # Return an HTML error page for web routes
    return render_template('error.html', error_message=f"An unexpected error occurred: {str(e)}"), 500

if __name__ == '__main__':
    app.run(debug=True)
