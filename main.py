import functions_framework
import requests
import textwrap
from flask import jsonify

# --- Helper Function: Fetches and Parses Card Data ---

def get_mtg_card_info(card_name):
    """
    Retrieves key information for a Magic: The Gathering card from the public API.

    Args:
        card_name (str): The name of the card to search for.

    Returns:
        dict: A dictionary with structured card info, or None if an error occurs.
    """
    base_url = "https://api.magicthegathering.io/v1/cards"
    params = {"name": card_name}

    try:
        response = requests.get(base_url, params=params)
        response.raise_for_status()  # Raise an exception for bad status codes (4xx or 5xx)
        data = response.json()

        # If the 'cards' list is empty, the card was not found
        if not data.get('cards'):
            return None

        # Take the first result, as the API can return multiple printings
        card_data = data['cards'][0]

        # Structure the data cleanly for the agent's response
        info = {
            "name": card_data.get('name'),
            "mana_cost": card_data.get('manaCost'),
            "type": card_data.get('type'),
            "text": card_data.get('text'),
            "power": card_data.get('power'),
            "toughness": card_data.get('toughness'),
            "image_url": card_data.get('imageUrl') # Added for potential display
        }
        return info

    except requests.exceptions.RequestException:
        # This catches network errors, timeouts, etc.
        return None
    except (KeyError, IndexError):
        # This catches issues with the API's response format
        return None

# --- Main Cloud Function Handler ---

@functions_framework.http
def mtg_card_tool(request):
    """
    An HTTP Cloud Function that acts as a tool for a Vertex AI Agent.
    It expects a JSON payload with a "card_name" key and returns card data.

    Args:
        request (flask.Request): The request object.

    Returns:
        flask.Response: A JSON response with card data or an error message.
    """
    # Verify the request is a POST request and has the correct content type
    if request.method != 'POST':
        return jsonify({"error": "Invalid request method. Please use POST."}), 405

    if not request.is_json:
        return jsonify({"error": "Invalid content type. Please send a JSON payload."}), 415

    # Get the JSON data from the request sent by the agent
    request_json = request.get_json(silent=True)

    # Validate that the required 'card_name' parameter is present
    if not request_json or "card_name" not in request_json:
        return jsonify({"error": "Missing 'card_name' in JSON payload."}), 400

    card_name = request_json["card_name"]

    # Use the helper function to get the card data
    card_data = get_mtg_card_info(card_name)

    if card_data:
        # Success: Return the structured data as a JSON response
        return jsonify(card_data), 200
    else:
        # Failure: Return a 404 Not Found error
        error_payload = {"error": f"Card '{card_name}' not found or API is unavailable."}
        return jsonify(error_payload), 404
