import os
os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'

import chainlit as cl
import requests
from dotenv import load_dotenv
from openai import OpenAI

# Load environment variables
load_dotenv()
gemini_api_key = os.getenv("GEMINI_API_KEY")

if not gemini_api_key:
    raise ValueError("❌ GEMINI_API_KEY is not set in .env file!")

# Initialize Gemini client
client = OpenAI(
    api_key=gemini_api_key,
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
)

def search_products(keyword: str):
    """Search products from API with better matching"""
    try:
        url = "https://hackathon-apis.vercel.app/api/products"
        response = requests.get(url, timeout=10)
        print(f"API Status: {response.status_code}")
        
        if response.status_code != 200:
            return []
            
        products = response.json()
        print(f"Total products: {len(products)}")
        
        # Debug: check first product structure
        if products:
            print("First product keys:", list(products[0].keys()))
        
        # Simple search implementation
        matched_products = []
        query_lower = keyword.lower().strip()
        
        for product in products:
            # Check all possible fields
            name = product.get("name", "").lower()
            title = product.get("title", "").lower()
            description = product.get("description", "").lower()
            category = product.get("category", "").lower()
            
            # Check if query exists in any field
            if (query_lower in name or 
                query_lower in title or 
                query_lower in description or
                query_lower in category):
                
                matched_products.append({
                    "name": product.get("name") or product.get("title", "Unknown Product"),
                    "price": product.get("price", "N/A"),
                    "image": product.get("image", ""),
                    "description": product.get("description", "")
                })
        
        print(f"Matches found: {len(matched_products)}")
        return matched_products[:8]

    except Exception as e:
        print(f"Search error: {e}")
        return []

async def get_ai_response(user_question: str):
    """Get response from Gemini AI"""
    try:
        response = client.chat.completions.create(
            model="gemini-2.0-flash",
            messages=[
                {
                    "role": "system", 
                    "content": "You are a helpful shopping assistant. Answer product questions helpfully and recommend relevant items from our catalog. Be friendly and informative."
                },
                {
                    "role": "user", 
                    "content": user_question
                }
            ],
            max_tokens=500
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"⚠️ Sorry, I encountered an error: {str(e)}"

@cl.on_chat_start
async def start():
    """Send welcome message when chat starts"""
    welcome_message = """
🛒 **Welcome to the AI Shopping Agent!**

I can help you find products and answer your shopping questions.

**Try asking me:**
- "Show me chairs or sofas"
- "What electronics do you have?"
- "Recommend home decor items"
- "Tell me about your products"

I'll search our catalog and provide helpful answers! 🤖
"""
    await cl.Message(content=welcome_message).send()

@cl.on_message
async def main(message: cl.Message):
    """Handle incoming messages"""
    user_question = message.content.strip()
    
    if not user_question:
        await cl.Message(content="❗ Please tell me what product you're looking for.").send()
        return

    # Show searching message
    search_msg = await cl.Message(content=f"🔍 Searching for '{user_question}'...").send()
    
    # Get both AI response and product results
    ai_response = await get_ai_response(user_question)
    product_results = search_products(user_question)
    
    # Build the response
    response_content = f"## 🤖 AI Shopping Assistant\n\n{ai_response}\n\n"
    
    # Add product results if available
    if product_results and len(product_results) > 0:
        response_content += f"## 🛍️ Found {len(product_results)} Matching Products\n\n"
        
        for i, product in enumerate(product_results, 1):
            response_content += f"### {i}. {product['name']}\n"
            response_content += f"**Price:** ${product['price']}\n"
            
            if product['image']:
                response_content += f"![Product Image]({product['image']})\n"
            
            if product['description']:
                response_content += f"{product['description'][:100]}...\n"
            
            response_content += "\n---\n\n"
    else:
        response_content += "## ❌ No exact matches found\n\n"
        response_content += "**Try these searches instead:**\n"
        response_content += "- sofa, chair, table\n"
        response_content += "- lamp, electronics, decor\n"
        response_content += "- home, office, kitchen\n"
    
    # Update the message with final results
    await search_msg.update(content=response_content)

if __name__ == "__main__":
    cl.run(port=8001)