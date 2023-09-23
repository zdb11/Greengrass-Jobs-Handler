# Greengrass jobs handler

### Why ?
If your component is responsible for handling jobs from AWS IoT Core on edge device you can do this in two ways. Constantly querying available jobs with API or MQTT topics or subscribing for "notify-next" MQTT reserved topic and waiting for the message about the next job. First approach will generate unnecessary cost and the second have a little flaw. If your edge device reconnects with clean [session](https://docs.aws.amazon.com/iot/latest/developerguide/mqtt.html#mqtt-persistent-sessions) (by default after 1 hour) all messages with QoS level 1 sent from AWS IoT Core will not reach your edge device, so the device will not get the message about next job. Then edge device should query for available jobs. But apparently, IPC Client V2 doesn't have any indicators when the connection to IoT Core MQTT is interrupted so the edge device doesn't know when it needs to do it. 

This little workaround helps to achieve that.

### How it's works ?
When your edge device reboots or reconnects with a clean session it's connecting IPC client and subscribing to topics. That produces messages in the reserved topic  '$aws/events/subscriptions/subscribed/+'. So basically it's your reconnect indicator. Now just create an IoT Core Rule to republish the message on the topic to which your component subscribes, getting that message for your edge device means it needs to query jobs. Simple as that. The example is written in Python but this workaround logic can be implemented in any other languages

# Example

### 1. Create IoT Core Rule

SQL statement 
```SQL
SELECT clientId FROM '$aws/events/subscriptions/subscribed/+' WHERE startswith(get(topics, 0), 'reconnect/')
```
Action 
Republish to AWS IoT Topic 
Topic
```
reconnect/{topic(5)}
```

Role policy
```javascript
{
    "Version": "2012-10-17",
    "Statement": {
        "Effect": "Allow",
        "Action": "iot:Publish",
        "Resource": "arn:aws:iot:<REGION>:<ACC NUMBER>:topic/reconnect/*"
    }
}
```
### 2. Add IoT Core policy to your thing certificate
```javascript
{
      "Effect": "Allow",
      "Action": [
        "iot:Publish"
      ],
      "Resource": [
        "arn:aws:iot:<REGION>:<ACC NUMBER>:topic/$aws/things/${iot:Connection.Thing.ThingName}/jobs/get",
      ]
    },
    {
      "Effect": "Allow",
      "Action": [
        "iot:Subscribe",
        "iot:Receive"
      ],
      "Resource": [
        "arn:aws:iot:<REGION>:<ACC NUMBER>:topicfilter/$aws/things/${iot:Connection.Thing.ThingName}/jobs/get/accepted",
        "arn:aws:iot:<REGION>:<ACC NUMBER>:topicfilter/$aws/things/${iot:Connection.Thing.ThingName}/jobs/notify-next",
        "arn:aws:iot:<REGION>:<ACC NUMBER>:topicfilter/reconnect/${iot:Connection.Thing.ThingName}"
      ]
    },
```
### 3. Build, publish and deploy custom component 
Install gdk cli
```sh
python3 -m pip install -U git+https://github.com/aws-greengrass/aws-greengrass-gdk-cli.git@v1.3.0
```
Change bucket and region in gdk-config.json file
Build component
```sh
gdk component build
```
Publish component
```sh
gdk component publish
```
Add GreengrassJobsHandler component in your next deployment to the edge device.

Now when your component reboots or reconnects with a clean session in GreengrassJobsHandler.log you will see logs about jobs.
# License

This repository is licensed under the Apache 2.0 License

