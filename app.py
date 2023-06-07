# Importing necessary modules
import os
from dotenv import load_dotenv
import openai
from presidio_analyzer import AnalyzerEngine
from presidio_anonymizer import AnonymizerEngine
import gradio as gr  # 3.32

# Load the environment variables from the local .env file
# NOTE: while using Jupyter Notebooks with VS Code, even when the .env
# is located in the root directory of the project, you must use ../.env
# instead of .env
load_dotenv()

# Check if the .env file exists in the Google Drive path
if os.path.exists("/content/drive/MyDrive/Projects/.env"):
    load_dotenv("/content/drive/MyDrive/Projects/.env")
    COLAB = True
    print("Note: using Google Colab")
else:
    COLAB = False
    print("Note: not using Google Colab")


# Retrieving API keys from the environment
openai.api_key = os.getenv("OPENAI_API_KEY")
username = os.getenv("PII_SAFE_CHAT_USERNAME")
password = os.getenv("PII_SAFE_CHAT_PASSWORD")


def analyze_and_anonymize(text: str):
    """
    Analyze and anonymize PII data from a given text string.

    Parameters
    ----------
    text : str
        The text to be analyzed and anonymized.

    Returns
    -------
    str
        The anonymized text.

    Example
    -------
    >>> text = "Mr. Smith's phone number is 212-555-5555, his SSN is \
    >>> 432-56-5654, and his credit card number is 344078656339539"
    >>> print(analyze_and_anonymize(text))
    """
    # Set up the engine, loads the NLP module (spaCy model by default)
    # and other PII recognizers
    analyzer = AnalyzerEngine()

    # Define the entities to analyze
    entities = [
        "CREDIT_CARD",
        "CRYPTO",
        "DATE_TIME",
        "EMAIL_ADDRESS",
        "IBAN_CODE",
        "IP_ADDRESS",
        "NRP",
        "LOCATION",
        "PERSON",
        "PHONE_NUMBER",
        "MEDICAL_LICENSE",
        "URL",
        "US_BANK_NUMBER",
        "US_DRIVER_LICENSE",
        "US_ITIN",
        "US_PASSPORT",
        "US_SSN",
    ]

    # Call analyzer to get results
    results = analyzer.analyze(text=text, entities=entities, language="en")

    # Analyzer results are passed to the AnonymizerEngine for
    # anonymization
    anonymizer = AnonymizerEngine()

    # Anonymize the text
    anonymized_text = anonymizer.anonymize(text=text, analyzer_results=results)

    return anonymized_text.text


def clear_history():
    """
    Clear the global variable `message_history`.

    This function resets the `message_history` list to its default
    state, which includes two messages: one from the user and one from
    the assistant.

    Notes
    -----
    This function directly modifies the global variable
    `message_history`.

    Examples
    --------
    >>> message_history
    [{'role': 'user', 'content': 'Hello!'}, {'role': 'assistant', 'content': 'Hello!'}]
    >>> clear_history()
    >>> message_history
    [{'role': 'user', 'content': 'You are an assistant.'}, {'role': 'assistant', 'content': 'OK'}]
    """
    # Declare that we're using the global variable `message_history`
    global message_history
    # Reset `message_history` to its default state
    message_history = [
        {"role": "user", "content": f"You are an assistant."},
        {"role": "assistant", "content": f"OK"},
    ]


# Initialize the `message_history` global variable to its default state
message_history = [
    {"role": "user", "content": f"You are an assistant."},
    {"role": "assistant", "content": f"OK"},
]


def predict(input):
    """
    Given a user's input, this function predicts a response by sending
    the anonymized input to the OpenAI API. This prediction is then
    appended to the message history. Finally, the function returns a
    list of pairs of consecutive messages from the history, skipping the
    pre-prompt.

    Parameters
    ----------
    input : str
        User's original input message

    Returns
    -------
    list
        A list of tuples. Each tuple contains a pair of consecutive
        messages from the message history.
    """

    # Anonymize the user input
    input_anonymized = analyze_and_anonymize(input)

    # Add the anonymized user input to the message history
    message_history.append(
        {
            "role": "user",
            "content": (f"{input_anonymized}"),
        }
    )

    # Get a completion from OpenAI's API based on the message history
    completion = openai.ChatCompletion.create(
        model="gpt-3.5-turbo", messages=message_history
    )

    # Extract the content of the reply from the API response
    reply_content = completion.choices[0].message.content

    # Add the reply content to the message history
    message_history.append(
        {"role": "assistant", "content": f"{reply_content}"}
    )

    # Generate a response by pairing consecutive messages in the
    # history, skipping the pre-prompt
    response = [
        (message_history[i]["content"], message_history[i + 1]["content"])
        for i in range(2, len(message_history) - 1, 2)
    ]

    # Return the response
    return response


# Start creating a Gradio Blocks interface with the 'darkhuggingface'
# theme
with gr.Blocks(theme="darkhuggingface") as demo:
    # Add a markdown element to the interface with introductory
    # information
    gr.Markdown(
        """
    ## Welcome to the PII-Safe Chat Application!  
    
    This interface replicates the functionality of ChatGPT-3, with an
    added layer of privacy protection. As you engage with the chat, our
    system proactively detects and anonymizes personally identifiable
    information (PII) before it ever reaches the ChatGPT API.

    For instance, let's say you input the following text:

    'Mr. Smith's phone number is 212-555-5555, and his SSN is
    432-56-5654, and his credit card number is 344078656339539'

    Our application is designed to recognize various PII entities within
    the text and anonymize them in a way that still maintains the
    context of the conversation. So, the message sent to the ChatGPT API
    would look like this:

    'Mr. <PERSON>'s phone number is <PHONE_NUMBER>, and his SSN is
    <US_SSN>, and his credit card number is <CREDIT_CARD>'

    This way, you can converse freely without concern about privacy
    breaches, while the AI continues to understand the essence of your
    message. Enjoy the chat!
    
    Here are some examples of the types of PII that our application can
    detect and anonymize:

    | PII Type                 | Example                                                                                   |
    |--------------------------|-------------------------------------------------------------------------------------------|
    | Credit Card              | "I just received my new credit card, it's 4532015112830366."                              |
    | Crypto Address           | "I've just set up a new Bitcoin wallet, the address is 1BvBMSEYstWetqTFn5Au4m4GFg7xJaNVN2."|
    | Date and Time            | "My birthday is on 15th August 1994, and the party starts at 7:30 PM."                    |
    | Email Address            | "For more information, please send an email to john.doe@example.com."                     |
    | IBAN Code                | "My international bank account number is DE44500105175407324931."                          |
    | IP Address               | "We need to whitelist this server's IP address, which is 192.168.1.1."                     |
    | UK NRP                   | "My UK National Insurance number is AB123456C."                                           |
    | Location                 | "I live in San Francisco, California."                                                     |
    | Person Name              | "My name is John Doe."                                                                    |
    | Phone Number             | "My contact number is +1 212-555-5555."                                                    |
    | Medical License Number   | "As a licensed physician, my medical license number is A123456."                           |
    | URL                      | "You can find more information on our website, www.example.com."                           |
    | US Bank Number           | "My bank routing number is 021000021."                                                     |
    | US Driver's License Number| "My driver's license number is B1234567."                                                 |
    | US ITIN                  | "As a non-resident alien, I have an Individual Taxpayer Identification Number, which is 912-34-5678."|
    | US Passport Number       | "My US passport number is C123456789."                                                     |
    | US Social Security Number| "My social security number is 123-45-6789."                                                |

    Here are a few examples of text that an employee might enter, which
    could contain various forms of personally identifiable information
    (PII)
    
    "I need to send an email to our client, Mr. John Doe, living at 123
    Main Street, Boston, MA. His policy number is NYL123 and his email
    address is [john.doe@example.com](mailto:john.doe@example.com). The
    email is regarding the new benefits of his Term Life Insurance
    policy."
    
    "Could you assist me in writing a letter to Mrs. Jane Smith? She
    resides at 456 Elm Street, San Francisco, CA. Her policy number is
    NYL456 and her date of birth is 1960-05-05. The letter is about the
    maturity benefits of her Whole Life Insurance policy."
    
    "I have to prepare a report for my manager, Mr. Robert Johnson.  His
    email address is
    [robert.johnson@newyorklife.com](mailto:robert.johnson@newyorklife.com).
    The report is about the performance of our Life Insurance products
    in Q1 2023."
        
    "I need to contact our client, Ms. Alice Williams. She lives at 789
    Pine Street, Chicago, IL. Her policy number is NYL789, and her phone
    number is (555) 555-5555. I need to inform her about the upcoming
    premium due date for her Universal Life Insurance policy."
        
    "Hello, I'm preparing an internal presentation about our client, Mr.
    Brian Lee. His date of birth is 1980-01-01, and he resides at 321
    Oak Street, Austin, TX. His policy number is NYL321. I'd like to
    highlight his positive feedback about our Variable Universal Life
    Insurance policy."

    Remember, our goal is to maintain the context of your conversations
    while ensuring your private information stays private. Enjoy
    chatting!
    """
    )

    # Create a chatbot component
    chatbot = gr.Chatbot()

    # Create a row layout for the textbox and the clear button
    with gr.Row():
        # Create a textbox for user input
        txt = gr.Textbox(
            show_label=False, placeholder="Enter text and press enter"
        ).style(container=False)

    # Create a button to clear the chat
    clear = gr.Button("New chat")

    # Add a submit event to the textbox that triggers the predict
    # function
    # The output is displayed in the chatbot component
    txt.submit(predict, txt, chatbot)

    # Add a submit event to the textbox that clears the textbox when
    # enter is pressed
    txt.submit(None, None, txt, _js="() => {''}")

    # Add a click event to the clear button that triggers the
    # clear_history function
    # The output is displayed in the chatbot component
    clear.click(clear_history, None, chatbot, queue=False)

# Launch the Gradio interface
demo.launch(
    #share=True,
    #auth=(username, password),
    #auth_message="Check your Login details sent to your email",
)
# demo.launch(share=True)
