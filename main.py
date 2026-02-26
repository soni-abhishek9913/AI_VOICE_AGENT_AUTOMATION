import asyncio
import base64
import json
import websockets
import os
from dotenv import load_dotenv
from pharmacy_fuction import FUNCTION_MAP, initialize_csv

load_dotenv()


def sts_connect():
    api_key = os.getenv("DEEPGRAM_API_KEY")
    if not api_key:
        raise Exception("DEEPGRAM_API_KEY not found in .env file")

    return websockets.connect(
        "wss://agent.deepgram.com/v1/agent/converse",
        subprotocols=["token", api_key]
    )


def load_config():
    with open("config.json", "r") as f:
        return json.load(f)


def execute_function_call(func_name, arguments):
    if func_name in FUNCTION_MAP:
        return FUNCTION_MAP[func_name](**arguments)
    return {"error": f"Unknown function: {func_name}"}


def create_function_call_response(func_id, func_name, result):
    return {
        "type": "FunctionCallResponse",
        "id": func_id,
        "name": func_name,
        "content": json.dumps(result)
    }


async def handle_function_call_request(decoded, sts_ws):
    for function_call in decoded.get("functions", []):
        func_name = function_call["name"]
        func_id = function_call["id"]
        arguments = json.loads(function_call["arguments"])

        result = execute_function_call(func_name, arguments)

        response = create_function_call_response(func_id, func_name, result)
        await sts_ws.send(json.dumps(response))


async def handle_text_message(decoded, sts_ws):
    if decoded.get("type") == "FunctionCallRequest":
        await handle_function_call_request(decoded, sts_ws)


async def sts_sender(sts_ws, audio_queue):
    while True:
        chunk = await audio_queue.get()
        
        await sts_ws.send(chunk)


async def sts_receiver(sts_ws, twilio_ws, streamsid_queue):
    streamsid = await streamsid_queue.get()

 

    async for message in sts_ws:
        if isinstance(message, str):
            decoded = json.loads(message)
            await handle_text_message(decoded, sts_ws)
            continue

        media_message = {
            "event": "media",
            "streamSid": streamsid,
            "media": {
                "payload": base64.b64encode(message).decode("ascii")
            }
        }

        await twilio_ws.send(json.dumps(media_message))


async def twilio_receiver(twilio_ws, audio_queue, streamsid_queue):
    BUFFER_SIZE = 160 * 20
    inbuffer = bytearray()

    async for message in twilio_ws:
        data = json.loads(message)
        event = data["event"]

        if event == "start":
            streamsid_queue.put_nowait(data["start"]["streamSid"])

        elif event == "media":
            chunk = base64.b64decode(data["media"]["payload"])
            if data["media"]["track"] == "inbound":
                inbuffer.extend(chunk)

        elif event == "stop":
            break

        while len(inbuffer) >= BUFFER_SIZE:
            audio_queue.put_nowait(inbuffer[:BUFFER_SIZE])
            inbuffer = inbuffer[BUFFER_SIZE:]


async def twilio_handler(twilio_ws):
    audio_queue = asyncio.Queue()
    streamsid_queue = asyncio.Queue()

    async with sts_connect() as sts_ws:
        await sts_ws.send(json.dumps(load_config()))

        await asyncio.gather(
            sts_sender(sts_ws, audio_queue),
            sts_receiver(sts_ws, twilio_ws, streamsid_queue),
            twilio_receiver(twilio_ws, audio_queue, streamsid_queue)
        )


async def main():
    initialize_csv()  
    server = await websockets.serve(twilio_handler, "localhost", 4444)
    print("Server started on ws://localhost:4444")
    await server.wait_closed()


if __name__ == "__main__":
    asyncio.run(main())