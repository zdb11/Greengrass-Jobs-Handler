import sys
import asyncio
import awsiot.greengrasscoreipc.clientv2 as clientV2

thing_name = sys.argv[1]

def handle_subscription(ipc_client: clientV2.GreengrassCoreIPCClientV2, topic_name: str, message: str):
    if topic_name == f"reconnect/{thing_name}":
        print("Handles reconnect event")
        topic = f"$aws/things/{thing_name}/jobs/get"
        ipc_client.publish_to_iot_core(topic_name=topic, qos=1, payload= "")
    elif topic_name == f"$aws/things/{thing_name}/jobs/get/accepted":
        print(f"Queried jobs message: {message}")
        #                                                           #
        # Here implement your logic to handle queried jobs message  #
        #                                                           #
    elif topic_name == f"$aws/things/{thing_name}/jobs/notify-next":
        print(f"Message about next job to do {message}")
        #                                                           #
        #   Here implement your logic to handle next job message    #
        #                                                           #

async def subscribe(ipc_client: clientV2.GreengrassCoreIPCClientV2, topic: str) -> None:
    def on_stream_event(event):
        try:
            topic_name = event.message.topic_name
            message = str(event.message.payload, "utf-8")
            print(f'Received new message on topic {topic_name}:  {message}')
            #                                                   #
            #          Implementation of handling logic         #
            #                                                   #
            handle_subscription(ipc_client, topic_name, message)
        except Exception as error:
            print(f"Can't handle subscription. Error: {error}")

    def on_stream_error(error):
        # Return True to close stream, False to keep stream open.
        return False

    def on_stream_closed():
        pass

    resp, operation = ipc_client.subscribe_to_iot_core_async(
        topic_name=topic,
        qos=1,
        on_stream_event=on_stream_event,
        on_stream_error=on_stream_error,
        on_stream_closed=on_stream_closed,
    )

async def subscribe_to_topics(ipc_client: clientV2.GreengrassCoreIPCClientV2, topics: list):
    tasks = []
    for topic in topics:
        print(f"Subscribing to {topic}")
        task = asyncio.ensure_future(subscribe(ipc_client, topic))
        tasks.append(task)

    await asyncio.gather(*tasks)
    while True:
        await asyncio.sleep(1)

def main():
    print(f"ThingName: {thing_name}")

    print(f"Connecting IPC Client")
    ipc_client = clientV2.GreengrassCoreIPCClientV2()
    topics = [f"$aws/things/{thing_name}/jobs/get/accepted", f"$aws/things/{thing_name}/jobs/notify-next", f"reconnect/{thing_name}"]
    print(f"Subscribing to topics: {topics}")
    asyncio.run(subscribe_to_topics(ipc_client=ipc_client, topics=topics))

if __name__ == "__main__":
    main()
