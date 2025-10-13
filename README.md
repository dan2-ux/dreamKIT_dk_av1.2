# This repository showcases the next version of dreamKIT_dk_av1.2

This is the AI-driven approach to the dreamKIT project, running will give AI more control over vss_dbc and enabling improved management.
It also serves as an update to the previous predecessor, dreamKIT_dk_av1.

## What is the difference from dreamKIT_dk_av1
Av1 depends on the user’s guidance and the number of functions it can call. Despite performing well, Av1 soon encounters scalability issues, as it is limited by the number of APIs it can understand or call, as well as the amount of guidance and functions that can be written.

Since vss_dbc contains around 600 APIs—each with different types requiring unique functions to either modify or retrieve their values—this complexity eventually leads to a dead end.

## Software requirement
- eclipse-autowrx
- kuksa_client
- langgraph/langchain
- RAG
- ollama
- Some llm models

**Warning**: If you are unfamiliar with eclipse-autowrx and kuksa_client, I highly encourage you to first learn about dreamKIT, which was designed and developed by Bosch’s team.

## Hardware requirement
You don't need to purchase extra tool, sensor or device to run this repository.
However, this was built on Ubuntu, so it may not run properly or may perform slowly on other operating systems.
Additionally, your device should have high computing power; otherwise, the LLM may not perform well.

## Workflow
The model require 3 LLM model which all have different responsabilit, which are named inside of the *define.json*.
- **tool_model**: reponsible for tool calling.
- **com_model**: is tasked with communicating normal conversation with user.
- **api_detect_model**: detecting api that is neccesary based on user command.

There are 2 main capabilities that this model can do. 
- The first one is **tell**, which means model can check current value of API through running sdv-runtime and kuksa_client.
- The next one is **set**, which means model can change vehicle value into something new according to user demmand.

When user said something if it contains special words like *time*, *date*, *set*, *change*, *turn*, *status*, tool_model will start analyzing that sentence then if user command model to **tell** or **set** then it will do it, but if not then it will answer normally. But if the sentence doesn't contains any *time*, *date*, *set*, *change*, *turn*, *status*, then **com_model** will run automatically.

**Warning**: this workflow is a summary of what model do, but this can only archive if sdv-runtime and kuksa-client is functioning.

## Guidance

### Step 1: Run the sdv-runtime natively on Pi 5

To start the SDV runtime, use the following command:

<pre>  docker run -it --rm -e RUNTIME_NAME="YOUR-NAME" -p 55555:55555 --name sdv-runtime ghcr.io/eclipse-autowrx/sdv-runtime:latest  </pre>

### Step 2: Download necesary LLM

If you did't install ollama on your computer yet, then run the following command download it.
<pre>
  ## For Linux
  curl -fsSL https://ollama.com/install.sh | sh
</pre>

To know what LLM models to install, open **define.json** file to see what model you should install, or you can configure the **define.json** and change models into your prefer models
<pre>
  # to install LLM model using ollama
  ollama pull the_model_name
</pre>

### Step 3: Build the docker image
First, you need to **cd** into the directory which help **dockerfile**. Then run the following command to build the image.
<pre>
  docker build -t dk_av1.2 .
</pre>

### Step 4: Run the docker image
This step is more sticky as ollama and its LLM is outside of docker reach, and it is difficult to build docker with running LLM in it. So we need to go around it by connecting docker enviroment to host, making LLM reachable for docker. Run the following command to enable it.
<pre>
  docker run -it --rm --network host -v $(pwd):/app -w /app dk_av1.2
</pre>

1. **docker run**: This tells Docker to create and run a new container from an image.

2. **-it**: This is actually two flags combined:

-i → interactive mode. Keeps STDIN open so you can interact with the container.

-t → allocate a pseudo-TTY. Gives you a terminal interface, making it feel like you’re inside a normal shell.

Together, -it is commonly used for interactive shells.

3. **--rm**: Automatically removes the container when it exits.

4. **--network host**: The container will share the same network interfaces as your host.

5. **-v $(pwd):/app**:

- -v mounts a volume (shared directory) between your host and the container.

- $(pwd) → the current working directory on your host.

- /app → the path inside the container where the host directory will be mounted.

This allows the container to read/write files directly in your host folder.

6. **-w /app**: Sets the working directory inside the container to /app.

7. **dk_av1.2**: This is the Docker image name you are running.

To access the tool calling AI. You should make sentence based on these words *time*, *date*, *set*, *change*, *turn*, *status*.
For example:
- To change low beam from off to on said: *turn low beam lights on* or *set low beam lights on*
- To tell AI to get vehicle value said: *status of driver seat position*

To know vehicle api name better check out the **data.csv**, or you can change that data inside it, to make api search suit your own speech habit.
However, when change the **data.csv** file you should delete **chroma_langchain_db1** which is contains the new value that AI look into. 


## How to deal with LLM model that doesn't have tool calling function
This is a tricky situation: most companies have removed tool-calling capabilities from their latest LLMs. However, tool calling remains a powerful way for an LLM to interact with the host computer, which is why this repository is built on that principle.

If your chosen model does not support tool calling, first open the modelfile_ai file and change the LLM name on the first line to the model you prefer. Once done, run the following command.

<pre>
  ollama create new-model-name -f modelfile-ai
</pre>
This works well on gemma model and it actually give them tool calling functionality, however other model may not perform as expected.


Demonstration video

file:///home/sdv-runtime/Videos/Screencasts/Screencast%20from%2010-13-2025%2009:55:28%20AM.webm






















