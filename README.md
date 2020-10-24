# ChatbotConcierge

AWS services based Dining Recommendation System

![Demo](https://github.com/sailikhithk/ChatbotConcierge/blob/main/ChatbotConcierge.png)

![Demo](https://github.com/sailikhithk/ChatbotConcierge/blob/main/ChatbotConcierge2.png)

# Architecture

![architecture](https://github.com/sailikhithk/ChatbotConcierge/blob/main/architecture.png)

**Dining Concierge Chat App**

Name: Ishan Tickoo, Sai Likhith Kanuparthi
NetID: it732, slk522

**S3 Bucket link:** 
**GitHub Release:** 

**Overview:**

Here we implement a serverless, microservice driven web application using AWS cloud Services. The chatbot provides recommendations for restaurants in the Manhattan area based on the cuisine type and various other factors like time, date etc. We have collected our data using the YELP-API.

**Services Used:**

1.	Amazon S3 - To host the frontend of our web application in an S3 bucket
2.	Amazon Lex - To create the bot and train it
3.	API Gateway - To set up the API
4.	Amazon SQS - to store user requests on a first-come bases (FIFO).
5.	Elasticsearch Service - To get restaurant ids based on the cuisine that the user prefers collected from SQS
6.	DynamoDB - To store the restaurant data in NoSQL format collected using Yelp API
7.	Amazon SNS – Used to send restaurant suggestions to users through SMS or email
8.	Lambda - To send data from the frontend to API and API to Lex, validation, collecting restaurant data, sending suggestions using SNS.
9.	Yelp API - To get suggestions for food
10.	AWS Cognito - For user authentication

**Steps:**

### 1.	Build and Deploy the Frontend application:
       a.We need to implement an interactive chat interface in which a user can write text and get a reply back. We have used open source frameworks and libraries that can work for our UI. link
       b.	We need to host the frontend in S3 bucket.
            ###### i.  Set up bucket for hosting. link
### 2.	Build the API for the application
       a.	Use API Gateway to setup your API 
          i.	 Use the following API/Swagger specification for your API 

                     ### swagger-  Use swagger editor to visualize this file 
                     * You can import the Swagger file into API Gateway 
                     * AWS API Gateway developer Guide
                     * Create a Lambda function (LF0) that performs the chat operation 1/7 
                     * Use the request/response model (interfaces) specified in the API specification above 
               ii. For now, just implement a boilerplate response to all messages: 
                     * ex. User says anything, Bot responds: "I’m still under development. Please come back later."
       b.	 Enable CORS on your API methods link
       c. Generate an SDK for your API link link
### 3. Build a Dining Concierge chatbot using Amazon Lex.
     ##### a. Create a new bot using the Amazon Lex service. Read up the documentation on all things Lex, for   more information: https://docs.aws.amazon.com/lex/latest/dg/getting-started.html
     ##### b. Create a Lambda function (LF1) and use it as a code hook for Lex, which essentially entails the invocation of your Lambda before Lex responds to any of your requests -- this gives you the chance to manipulate and validate parameters as well as format the bot’s responses. More documentation on Lambda code hooks at the following link: https://docs.aws.amazon.com/lex/latest/dg/using-lambda.html
    ##### c. Bot requirements:
        i.  Implement at least the following three intents:
            •	GreetingIntent
            •	ThankYouIntent
            •	DiningSuggestionsIntent
        ii. The implementation of an intent entails its setup in Amazon Lex as well as handling its response in the Lambda function code hook.
            * Example: GreetingIntent:
            •	create the intent in Lex, 
            •	train and test the intent in the Lex console, 
            •	 implement the handler for the GreetingIntent in the Lambda code hook, such that when you receive a request for the GreetingIntent you compose a response such as “Hi there, how can I help?”

         iii. For the DiningSuggestionsIntent, you need to collect at least the following pieces of information from the user, through conversation:
            •	Location
            •	Cuisine
            •	Dining Time
            •	Number of people
            •	Phone number
     iv. Based on the parameters collected from the user, push the information collected from the user (location, cuisine, etc.) to an SQS queue (Q1). More on SQS queues here: link
            Also confirm to the user that you received their request and that you will notify them over SMS once you have the list of restaurant suggestions.
### 4. Integrate the Lex chatbot into your chat API
##### a. Use the AWS SDK to call your Lex chatbot from the API Lambda (LF0).
##### b. When the API receives a request, you should 
        •	extract the text message from the API request, 
        •	send it to your Lex chatbot, 
        •	wait for the response, 
        •	send back the response from Lex as the API response.
### 5. Use the Yelp API to collect 5,000+ random restaurants from Manhattan.
##### i. Yelp API
        •	Get restaurants by your self-defined cuisine types
        •	You can do this by adding cuisine type in the search term ( ex. Term: chinese restaurants)
        •	Each cuisine type should have 1,000 restaurants or so.
        •	Make sure your restaurants don’t duplicate.
##### ii. DynamoDB (a noSQL database)
        •	Create a DynamoDB table and named “yelp-restaurants”
        •	Store the restaurants you scrape, in DynamoDB (one thing you will notice is that some restaurants might have more or ess fields than others, which makes DynamoDB ideal for storing this data)
        •	With each item you store, make sure to attach a key to the object named “insertedAtTimestamp” with the value of the time and date of when you inserted the particular record 
        •	Store those that are necessary for your recommendation.(Requirements: Business ID, Name, Address, Coordinates, Number of Reviews, Rating, Zip Code)
##### iii. Note: you can perform this scraping from your computer or from your AWS account -- your pick.
### 6.	Create an ElasticSearch instance using the AWS ElasticSearch Service.
        o	Create an ElasticSearch index called “restaurants”
        o	Create an ElasticSearch type under the index “restaurants” called “Restaurant”
        o	Store partial information for each restaurant scraped in ElasticSearch under the “restaurants” index, where each entry has a “Restaurant” data type. This data type will be of composite type stored as JSON in ElasticSearch. https://www.elastic.co/guide/en/elasticsearch/guide/current/mapping.html
        o	You only need to store RestaurantID and Cuisine for each restaurant
### 7.	Build a suggestions module, that is decoupled from the Lex chatbot.
    a.	Create a new Lambda function (LF2) that acts as a queue worker. Whenever it is invoked it
        •	pulls a message from the SQS queue (Q1),
        •	gets a random restaurant recommendation for the cuisine collected through conversation from Elasticsearch and DynamoDB,
        •	formats them and sends them over text message to the phone number included in the SQS message, using SNS (https://docs.aws.amazon.com/sns/latest/dg/SMSMessages.html).
        •	Use the DynamoDB table “yelp-restaurants” (which you created from Step 1) to fetch more information about the restaurants (restaurant name, address, etc.), since the restaurants stored in Elasticsearch will have only a small subset of fields from each restaurant. 
        •	Modify the rest of the LF2 function if necessary to send the user text/email.
     b.	Set up a CloudWatch event trigger that runs every minute and invokes the Lambda function as a result: https://docs.aws.amazon.com/AmazonCloudWatch/latest/events/RunLabdaSchedule.html. This automates the queue worker Lambda to poll and process suggestion requests on its own.





