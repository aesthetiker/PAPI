from flask import Flask, render_template, request, redirect, url_for, jsonify
import requests
import json
import logging
from datetime import datetime, timedelta

app = Flask(__name__)

# Configure logging
logging.basicConfig(level=logging.DEBUG)

# OAuth 2.0 Configuration
TOKEN_URL = "https://partner.preprod.flexilis.com/oauth2/token"
REFRESH_TOKEN_URL = "https://partner.preprod.flexilis.com/oauth2/token"
PARTNER_CP_KEY = "eyJraWQiOiI2YTo1ZDphNTphNDo0MDpjYTowMDozNzowOTpmYjo4NzoyMDo1NDphMzo0NjpjZjphZjoyODo1MDplNTowMzplOTo4NDo1MDplOTowMTo5Mzo2ZTo2OToxNDo3OTo3NyIsImN0eSI6IkpXUyIsImVuYyI6IkExMjhHQ00iLCJhbGciOiJSU0EtT0FFUC0yNTYifQ.ocqT6sd7B-dhJ_q_DwTP1PcJjh5NZkJRt0_wemCRMpJyIonAJ72_DoS0gWD_m31umtuVIXD0Tx-rfjYciBlCoKetb0C9uUdSZzcEEKP6xZVEZ3iB3g6zUDAKf3yctvaJrPYv3us5kRF00ISIEA4CUKxb5Q7Kpgwi29lDGIBgt4f4iyM90ERTXHFLfxlrz6v8FK6B2q9YIUeOPbFlFQUSwpEmxUdYkAFJsWc7VlSA1FPIN4l_EblsP1-LWh8cOcfqIGS99MMNsjZFp7aceQEk3-lU_2oVSwB6G4IFmomNY4UzrdZCRQQ7WSscZECuAljvrTIAjh4qoyhCiJ0V7YKcs1GO2LcuvSYRTFPnwwibxSOi1bK8wTLWDt0iMmvUNcLrfWEipiOb7DZXxjpjdzuDIWvhHuKOzjGlxSzXAOS0TGcVmaKS4Ndo_4lGqECQ5VJIfGK4axr0FFB7CNjZWT2zcGXGOrFNn_3nOX97_kbjpgp9NQ0ZcmmipSxtzKjalcXrNzrZau7BroCt40e_acs2zLIDnluGboRdDT1RQsLVPyZYd81ywokroivtWWZm22vnneJunK5Ums5oabC10JihFhaZFENEZr06Br0wMpbG-KjEoA0MdjOQpref_rvTFAn86VW3BvYcAxzK_rUHyymOjqofblhEwUXyGx-QL1YHANI.Djatuup2mwFFuQTz.If0iqYR3P4QsLy8m8GxLMYrWrDuWCTl3xSFDxLWl5uY_FPG29cy3jQB0WuUIIa-cPodqpeGYOOyvCr-QxEdzWX2x_IGr8OwOC4MyPJRTVDIBTnxbVrJbKYDKBRRuAY1q7DabuVwX9Og_hwRguYShz24M_psNbEyaWefGwsbiMVEjVKFGNzbLv1H4gvTTw4IDCjDlfaRNIY8aR7kLX22A8J2BKzNP_iIyH5uCqDf3gtMgkR1mcyexXTEjmqD5j2cEaZS--hDD0PjXUCq1n6bWv0QRkleAGFBEVrAWxyOtNGmF6ddb73bfb6FFUDrgcRjIIyGaD0hJm6Gd4m0P8sWfWP-zpaBwj071mnzOyix9LQ1spYJez8QixnMcPPH9wf_5VGxQVSBZBlKGUp_IA10LjdhmGdfSnTeL3eC_Jq_yrpd7QBm3dizwsL3hmKKUk_akSnjMYGWlZlrbkXq3frHtWPK7616hL0XFw8U3GYTj1cPb840Phc7LBmONp65jVSuntP7pqGPVVZr5PVVr8hdAnGPNExqoFwfJeOf8UUixMKn0nEVmGa5-ZItR7-oh6CcjP5j6LJdC4azJuGoqejxrAJoqS3Up77pJRWAA7WYXYtLgPwgfB4hK6zFYeo4e_jbFI-iritMgJ2NXOnw-5-gFxWZpJW277kwRPDvomZLfr8UwUnXmEAML1mfHGQC5pJzauh0FhQ_yZXvk_quYa9MBCc_hSIbA3Hkf7CyVyazi_eb-CQgMIvf5hJmIqDH7u7PJVGtfCuOIjde3IdFwX2zOo4ZCrvMoUfibI2rhTgw2vjtsxIjniipdSP4sZNix16Ttj4zP_Xc0zecpuWhHhI0I135M5r6naabuVSda0xA7uGPpK9wXfUjxRVHSAU1zL4ptjeHa5GGFoRyglQin3rYykWJTnhNvrp_MwQJL6nDhTPPoL1xsThQWPTxph2yU9oYmvOVzy8mxxjfK5jkh6Mh8pcH81_mBZiGLsNOHE5wJVmG5qDLbTDM2LuTvZFEdGyJlgfzGG4MciPi1YxM98UpSezT28nbXTGXBwp_TN-mcujGIoQhivWWTSTi5ISTYIS2L1FZrH7ayPyxxOaMSeUXmaFMITkmo3x6EpcHbm24I9pu1fx4hE-NEvI_hUI-nhSlPuGm3hWYIrX_NHo1CzAxWu3NNf_PueepTqJJ6M6qalPu1iED7Udic4eY9j_etKt3P6qMBr4gHcLFFyJ3-gIepf-wsMCzRQsFEiozLyMKi8rAVSGoVGS8ztK1GjOLissbyX-6omljqAv-R1lM1IjGuxdCuadWk-j7gTtVvSiYw0uMfCXgY8k379AB94oUdWdjSyIum9TLid9MNvmTDJ_ijrw0BDcs2sDWwpNK5dtIv-s91on0XJZMHAzdTOHuwdDroRL_36NRUfduhtlRq4GISJ2Q8pdy0BurSIk1S7l3TAzEGHRF9pdMj7vlRfcSIOQhZ54eaP8aWPaHlaiAo2UEHmvb_EsISnxgGfHxjEXZ3OhoJAu8neHlTzlmIk4xeZC1ELwaVqbCr574DTY7bUXunKhwmIutAZCZ7IZq_NgH6kFo3amAayc_ZqHRSiqJMU2jPVGDR3_nPqsjgvjj7E7lsbhzPpfXsl7iFjiBg3qIPswLFqhJYgUCv6mqH6Cl-ro2_JTV6HI0ISA._UmjySP_gnYcRA7esVIv6w"

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

def refresh_access_token():
    global token_data
    data = {
        "grant_type": "refresh_token",
        "refresh_token": token_data["refresh_token"]
    }
    
    headers = {
        "Accept": "application/json",
        "Authorization": f"Bearer {PARTNER_CP_KEY}"
    }
    
    try:
        response = requests.post(REFRESH_TOKEN_URL, data=data, headers=headers)
        response.raise_for_status()
        new_token_data = response.json()
        token_data["access_token"] = new_token_data.get("access_token")
        token_data["refresh_token"] = new_token_data.get("refresh_token", token_data["refresh_token"])
        token_data["expires_at"] = datetime.now() + timedelta(seconds=new_token_data.get("expires_in", 3600))
        return token_data["access_token"]
    except requests.exceptions.RequestException as e:
        logging.error(f"Error refreshing access token: {str(e)}")
        token_data = {"access_token": None, "refresh_token": None, "expires_at": None}
        return None

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
        response = requests.get(f"{API_BASE_URL}/api/partners/v1/tenants?offset=0&limit=20", headers=headers)
        response.raise_for_status()
        logging.debug(f"API Response Content: {response.content}")
        
        if not response.content:
            return render_template('error.html', error_message="Empty response from API")
        
        tenants_data = response.json()
        tenants = tenants_data.get('tenants', [])
        return render_template('index.html', tenants=tenants)
    except requests.exceptions.RequestException as e:
        error_message = f"Error fetching tenants: {str(e)}"
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

@app.route('/api/tenant/<tenant_id>', methods=['GET'])
def get_tenant(tenant_id):
    access_token = get_access_token()
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Accept": "application/json"
    }
    
    try:
        response = requests.get(f"{API_BASE_URL}/api/partners/v1/tenants/{tenant_id}", headers=headers)
        response.raise_for_status()
        return jsonify(response.json()), 200
    except requests.exceptions.RequestException as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/tenant/<tenant_id>', methods=['PUT'])
def update_tenant(tenant_id):
    access_token = get_access_token()
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Accept": "application/json",
        "Content-Type": "application/json"
    }
    
    try:
        data = request.json
        response = requests.put(f"{API_BASE_URL}/api/partners/v1/tenants/{tenant_id}", headers=headers, json=data)
        response.raise_for_status()
        return jsonify(response.json()), 200
    except requests.exceptions.RequestException as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/tenant/<tenant_id>/cancel_order/<order_id>', methods=['PATCH'])
def cancel_order(tenant_id, order_id):
    access_token = get_access_token()
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Accept": "application/json",
        "Content-Type": "application/json"
    }
    
    cancel_data = {
        "status": "cancelled",
        "transactionId": request.json.get('transactionId'),
        "externalPartnerId": request.json.get('externalPartnerId'),
        "skus": request.json.get('skus'),
        "productType": request.json.get('productType'),
        "commercialPartnerName": request.json.get('commercialPartnerName')
    }
    
    try:
        response = requests.patch(f"{API_BASE_URL}/api/partners/v1/tenants/{tenant_id}/orders/{order_id}",
                                headers=headers, json=cancel_data)
        response.raise_for_status()
        return jsonify({"message": "Order cancelled successfully"}), 200
    except requests.exceptions.RequestException as e:
        error_message = f"Error cancelling order: {str(e)}"
        logging.error(error_message)
        return jsonify({"error": error_message}), 500

@app.route('/api/new_order', methods=['POST'])
def create_new_order():
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
        required_fields = ["transactionId", "externalPartnerId", "skus", "termType", 
                          "termLength", "seatTotal", "contactEmail", "companyName"]
        missing_fields = [field for field in required_fields if field not in data or not data[field]]
        
        if missing_fields:
            logging.error(f"Missing required fields: {missing_fields}")
            return jsonify({"error": f"Missing required fields: {', '.join(missing_fields)}"}), 400
        
        # Handle managed field logic
        if data.get("managed") == "true" and not data.get("externalOrgId"):
            logging.error("Managed is set to true but no externalOrgId provided")
            return jsonify({"error": "When managed is true, externalOrgId must be provided"}), 400
        
        # Make the API request
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

@app.route('/api/orgs', methods=['GET'])
def get_orgs():
    access_token = get_access_token()
    if not access_token:
        return jsonify({"error": "Failed to obtain access token"}), 401
    
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Accept": "application/json"
    }
    
    try:
        response = requests.get(f"{API_BASE_URL}/api/partners/v1/orgs", headers=headers)
        response.raise_for_status()
        logging.debug(f"Organizations response: {response.json()}")
        return jsonify(response.json()), 200
    except requests.exceptions.RequestException as e:
        error_message = f"Error fetching organizations: {str(e)}"
        logging.error(error_message)
        return jsonify({"error": error_message}), 500

@app.route('/api/partners/v1/orgs/<org_id>', methods=['GET'])
def get_org_details(org_id):
    access_token = get_access_token()
    if not access_token:
        return jsonify({"error": "Failed to obtain access token"}), 401
    
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Accept": "application/json"
    }
    
    try:
        response = requests.get(f"{API_BASE_URL}/api/partners/v1/orgs/{org_id}", headers=headers)
        response.raise_for_status()
        return jsonify(response.json()), 200
    except requests.exceptions.RequestException as e:
        error_message = f"Error fetching organization details: {str(e)}"
        logging.error(error_message)
        return jsonify({"error": error_message}), 500

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
