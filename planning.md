# FitFindr — planning.md

> Complete this document before writing any implementation code.
> Your spec and agent diagram are what you'll use to direct AI tools (Claude, Copilot, etc.) to generate your implementation — the more specific they are, the more useful the generated code will be.
> Your planning.md will be reviewed as part of your submission.
> Update it before starting any stretch features.

---

## Tools

List every tool your agent will use. For each tool, fill in all four fields.
You must have at least 3 tools. The three required tools are listed — add any additional tools below them.

### Tool 1: search_listings

**What it does:**
<!-- Describe what this tool does in 1–2 sentences -->
This tool searches amongst the listings.json file for items that match the user's description. 

**Input parameters:**
<!-- List each parameter, its type, and what it represents -->
- `description` (str): This contains keywords that describe what the user wants
- `size` (str): This is the size of the article the user wants, used to filter (None if the user doesn't specify size)
- `max_price` (float): This is the maximum price the user is willing to pay for the clothing inclusive, used to filter (None if the user doesn't have a max price)

**What it returns:**
<!-- Describe the return value — what fields does a result contain? -->
A list of matching dictionaries is returned and sorted by relevance (best match is first). 

**What happens if it fails or returns nothing:**
<!-- What should the agent do if no listings match? -->
An empty list is returned if nothing matches. 

---

### Tool 2: suggest_outfit

**What it does:**
<!-- Describe what this tool does in 1–2 sentences -->
This tool suggests 1-2 complete outfits given the user's wardrobe and the new clothing item from Tool 1.

**Input parameters:**
<!-- List each parameter, its type, and what it represents -->
- `new_item` (dict): The new clothing item that was returned from tool 1.
- `wardrobe` (dict): The user's existing wardrobe, may be empty.

**What it returns:**
<!-- Describe the return value -->
A nonempty string with outfit suggestions is returned. If the wardrobe is empty, general styling advice is returned.

**What happens if it fails or returns nothing:**
<!-- What should the agent do if the wardrobe is empty or no outfit can be suggested? -->
If the wardrobe is empty, general styling advice is returned.

---

### Tool 3: create_fit_card

**What it does:**
<!-- Describe what this tool does in 1–2 sentences -->
With the information from tool 2, this tool generates a shareable caption of the overall fit.

**Input parameters:**
<!-- List each parameter, its type, and what it represents -->
- `outfit` (str): The returned result from suggest_outfit.
- `new_item` (dict): The dictionary for the new item.

**What it returns:**
<!-- Describe the return value -->
A string that's usable as a caption is returned.

**What happens if it fails or returns nothing:**
<!-- What should the agent do if the outfit data is incomplete? -->
If the outfit is empty or missing, an error message string is returned.

---

### Additional Tools (if any)

<!-- Copy the block above for any tools beyond the required three -->

---

## Planning Loop

**How does your agent decide which tool to call next?**
<!-- Describe the logic your planning loop uses. What does it look at? What conditions change its behavior? How does it know when it's done? -->
The agent first calls search_listings with the user's query. If the resulting list is empty, set an error message in the session and return early. If it's not empty, then set the selected item to be result[0] and pass that in as a parameter into suggest_outfit. If the wardrobe is empty for suggest_outfit, general styling advice is returned, and the procedure is stopped. Otherwise, suggest_outfit suggests outfits for the user using the selected item from the first tool. Then, using this suggestion, create_fit_card is called with this result passed in as outfit and the item from result[0] in search_listings passed in as new_item. If the outfit is empty or missing, an error message string is returned. Otherwise, a 2-4 sentence social media caption is created describing the fit. 

---

## State Management

**How does information from one tool get passed to the next?**
<!-- Describe how your agent stores and accesses state within a session. What data is tracked? How is it passed between tool calls? -->
The results of a tool call are appended to the initial call to the tool and passed back into the model to provide context for the next step of the process.

---

## Error Handling

For each tool, describe the specific failure mode you're handling and what the agent does in response.

| Tool | Failure mode | Agent response |
|------|-------------|----------------|
| search_listings | No results match the query | No listings were found in listings.json that match the user's query |
| suggest_outfit | Wardrobe is empty | Suggest to the user general clothing outfits that would go well with the new_item input parameter |
| create_fit_card | Outfit input is missing or incomplete | Return the error message string "There was no outfit suggestion, so no caption can be created". DO NOT throw an exception. |

---

## Architecture

<!-- Draw a diagram of your agent showing how the components connect:
     User input → Planning Loop → Tools (search_listings, suggest_outfit, create_fit_card)
                                                                          ↕
                                                                   State / Session
     Show what triggers each tool, how state flows between them, and where error paths branch off.
     ASCII art, a Mermaid diagram (https://mermaid.js.org/syntax/flowchart.html), or an embedded
     sketch are all fine. You'll share this diagram with an AI tool when asking it to implement
     the planning loop and each individual tool. -->

```
User query
    │
    ▼
Planning Loop ───────────────────────────────────────────┐
    │                                                    │
    ├─► search_listings(description, size, max_price)    │
    │       │ results=[]                                 │
    │       ├──► [ERROR] "No listings found..." → return │
    │       │                                            │
    │       │ results=[item, ...]                        │
    │       ▼                                            │
    │   Session: selected_item = results[0]              │
    │       │                                            │
    ├─► suggest_outfit(selected_item, wardrobe)          │
    │       │                                            │
    │   Session: outfit_suggestion = "..."               │
    │       │                                            │
    └─► create_fit_card(outfit_suggestion, selected_item)│
            │                                            │
        Session: fit_card = "..."                        │
            │                                            └─ error path returns here
            ▼
        Return session

```
---

## AI Tool Plan

<!-- For each part of the implementation below, describe:
     - Which AI tool you plan to use (Claude, Copilot, ChatGPT, etc.)
     - What you'll give it as input (which sections of this planning.md, your agent diagram)
     - What you expect it to produce
     - How you'll verify the output matches your spec before moving on

     "I'll use AI to help me code" is not a plan.
     "I'll give Claude my Tool 1 spec (inputs, return value, failure mode) and ask it to implement
     search_listings() using load_listings() from the data loader — then test it against 3 queries
     before trusting it" is a plan. -->

**Milestone 3 — Individual tool implementations:**
I will use Claude. I will paste in the tool specs in this markdown file and ask it to immplement the code in tools.py. Then, I will ask it to test it with the different edge cases and regular queries as well.

**Milestone 4 — Planning loop and state management:**
I will use Claude. I will give the example walkthrough at the bottom of this file and my architecture diagram, and Claude should output code that mimics this procedure.

---

## A Complete Interaction (Step by Step)

Write out what a full user interaction looks like from start to finish — tool call by tool call. Use a specific example query.

**Example user query:** "I'm looking for a vintage graphic tee under $30. I mostly wear baggy jeans and chunky sneakers. What's out there and how would I style it?"

**Step 1:**
<!-- What does the agent do first? Which tool is called? With what input? -->
Search: search_listings() is called with inputs "vintage graphic tee" as the descipriton, size is None, and max_price is 30.

**Step 2:**
<!-- What happens next? What was returned from step 1? What tool is called now? -->
From step 1, a list of matching dicts is returned, sorted by relevance. If the output is an empty list, FitFindr tells the user what to try differently and stops. If the output is not empty, call suggest_outfit tool. The inputs to this are new_item = output from step 1, wardrobe = user's wardrobe.

**Step 3:**
<!-- Continue until the full interaction is complete -->
The create_fit_card() tool is called with outfit = output from step 2 and new_item as output from step 1 for the inputs to the tool.

**Final output to user:**
<!-- What does the user actually see at the end? -->
The user sees the output of step 3 (a fit is created) at the end.
