from flask import Flask, request, Response
from twilio.rest import Client
from twilio.twiml.voice_response import VoiceResponse
import openai
import requests

# ---------------- CONFIG ----------------
openai.api_key = "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"
ELEVENLABS_API_KEY = "sk_58bd3e618c143bcfd107a251c175c646195e9c9c082e177f"
VOICE_ID = "dMyQqiVXTU80dDl2eNK8"

TWILIO_ACCOUNT_SID = "ACb8a11f788ee8a8586fe65e31715f0c94"
TWILIO_AUTH_TOKEN = "765d81ce417032c45bd7254059624472"
TWILIO_NUMBER = "+14256751266"
CUSTOMER_NUMBER = "+916380479664"

PRODUCT_INFO = """
Color: Black
Fabric: Cotton
Fit: Relaxed Fit
Occasion: Casual
Length: Regular
Closure: Button and Zip
Waist Rise: Mid-Rise
Reversible: No
Wash Care: Machine Wash
Usage: Casual
"""

app = Flask(__name__)

def ask_gpt(question):
    try:
        context = f"""You are a helpful, empathetic customer support assistant.
Product details:
{PRODUCT_INFO}
Instructions:
- If the customer mentions fit or size issues, suggest sizing up by 1-2 sizes or reassure that returns/exchanges are easy.
- Never tell them to check the size chart.
- Respond in a human, empathetic tone.
"""
        response = openai.chat.completions.create(
            model="gpt-5-mini",
            messages=[
                {"role": "system", "content": context},
                {"role": "user", "content": question}
            ]
        )
        return response.choices[0].message.content
    except Exception as e:
        print("Error in ask_gpt:", e)
        return "Sorry, I cannot answer right now."


def text_to_speech(text):
    try:
        url = f"https://api.elevenlabs.io/v1/text-to-speech/{VOICE_ID}"
        headers = {"xi-api-key": ELEVENLABS_API_KEY, "Content-Type": "application/json"}
        data = {"text": text}
        response = requests.post(url, json=data, headers=headers)

        if response.status_code != 200:
            print("ElevenLabs error:", response.status_code, response.text)
            return None

        audio_file = "response.mp3"
        file_path = f"static/{audio_file}"
        with open(file_path, "wb") as f:
            f.write(response.content)
        return audio_file
    except Exception as e:
        print("Exception in text_to_speech:", e)
        return None




@app.route("/voice-handler", methods=["POST"])
def voice_handler():
    resp = VoiceResponse()
    resp.say("Hi! This is a quick call from our store. You can ask questions about your order.", voice="alice")
    resp.gather(input="speech", action="/process-question", speechTimeout="auto")
    return Response(str(resp), mimetype="text/xml")

@app.route("/process-question", methods=["POST"])
def process_question():
    try:
        resp = VoiceResponse()
        customer_question = request.form.get("SpeechResult", "")
        print("Customer asked:", customer_question)

        if not customer_question:
            resp.say("Sorry, I did not catch that. Please say it again.", voice="alice")
        else:
            # Ask GPT safely
            answer = ask_gpt(customer_question)
            print("Answer:", answer)
            # Speak the GPT answer
            resp.say(answer, voice="alice")

        # Ask for more questions
        resp.gather(input="speech", action="/process-question", speechTimeout="auto")
        return Response(str(resp), mimetype="text/xml")
    
    except Exception as e:
        print("Error in /process-question:", e)
        # Fallback response if something goes wrong
        fallback_resp = VoiceResponse()
        fallback_resp.say("Sorry, an error occurred. Please try again.", voice="alice")
        fallback_resp.gather(input="speech", action="/process-question", speechTimeout="auto")
        return Response(str(fallback_resp), mimetype="text/xml")


def trigger_call():
    client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
    call = client.calls.create(
        to=CUSTOMER_NUMBER,
        from_=TWILIO_NUMBER,
        url="https://jovita-reviewable-kaye.ngrok-free.dev/voice-handler"
    )
    print("Call triggered successfully!")

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "call":
        trigger_call()
    else:
        app.run(host="0.0.0.0", port=5000)
