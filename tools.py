"""
tools.py

The three required FitFindr tools. Each tool is a standalone function that
can be called and tested independently before being wired into the agent loop.

Complete and test each tool before moving to agent.py.

Tools:
    search_listings(description, size, max_price)  → list[dict]
    suggest_outfit(new_item, wardrobe)              → str
    create_fit_card(outfit, new_item)               → str
"""

import os
import re

from dotenv import load_dotenv
from groq import Groq

from utils.data_loader import load_listings

load_dotenv()

# Common words that carry no search signal — dropped before keyword scoring.
_STOPWORDS = {
    "a", "an", "the", "and", "or", "for", "with", "to", "of", "in", "on",
    "under", "over", "some", "any", "looking", "want", "need", "find",
    "size", "im", "i", "my", "me", "that", "this", "is", "are", "be",
}


def _tokenize(text: str) -> list[str]:
    """Lowercase a string and split it into meaningful word tokens."""
    words = re.findall(r"[a-z0-9]+", text.lower())
    return [w for w in words if len(w) > 1 and w not in _STOPWORDS]


# ── Groq client ───────────────────────────────────────────────────────────────

def _get_groq_client():
    """Initialize and return a Groq client using GROQ_API_KEY from .env."""
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise ValueError(
            "GROQ_API_KEY not set. Add it to a .env file in the project root."
        )
    return Groq(api_key=api_key)


# ── Tool 1: search_listings ───────────────────────────────────────────────────

def search_listings(
    description: str,
    size: str | None = None,
    max_price: float | None = None,
) -> list[dict]:
    """
    Search the mock listings dataset for items matching the description,
    optional size, and optional price ceiling.

    Args:
        description: Keywords describing what the user is looking for
                     (e.g., "vintage graphic tee").
        size:        Size string to filter by, or None to skip size filtering.
                     Matching is case-insensitive (e.g., "M" matches "S/M").
        max_price:   Maximum price (inclusive), or None to skip price filtering.

    Returns:
        A list of matching listing dicts, sorted by relevance (best match first).
        Returns an empty list if nothing matches — does NOT raise an exception.

    Each listing dict has the following fields:
        id, title, description, category, style_tags (list), size,
        condition, price (float), colors (list), brand, platform

    TODO:
        1. Load all listings with load_listings().
        2. Filter by max_price and size (if provided).
        3. Score each remaining listing by keyword overlap with `description`.
        4. Drop any listings with a score of 0 (no relevant matches).
        5. Sort by score, highest first, and return the listing dicts.

    Before writing code, fill in the Tool 1 section of planning.md.
    """
    # 1. Load the full dataset.
    listings = load_listings()

    keywords = _tokenize(description)

    scored: list[tuple[int, dict]] = []
    for listing in listings:
        # 2. Apply the hard filters first — price ceiling and size.
        if max_price is not None and listing["price"] > max_price:
            continue
        if size is not None and size.lower() not in listing["size"].lower():
            continue

        # 3. Score by keyword overlap against the listing's searchable text.
        searchable = " ".join([
            listing["title"],
            listing["description"],
            listing["category"],
            " ".join(listing["style_tags"]),
            " ".join(listing["colors"]),
            listing["brand"] or "",
        ])
        searchable_tokens = set(_tokenize(searchable))
        score = sum(1 for kw in keywords if kw in searchable_tokens)

        # 4. Drop listings with no keyword overlap.
        if score > 0:
            scored.append((score, listing))

    # 5. Sort by score, highest first, and return just the listing dicts.
    scored.sort(key=lambda pair: pair[0], reverse=True)
    return [listing for _, listing in scored]


# ── Tool 2: suggest_outfit ────────────────────────────────────────────────────

def suggest_outfit(new_item: dict, wardrobe: dict) -> str:
    """
    Given a thrifted item and the user's wardrobe, suggest 1–2 complete outfits.

    Args:
        new_item: A listing dict (the item the user is considering buying).
        wardrobe: A wardrobe dict with an 'items' key containing a list of
                  wardrobe item dicts. May be empty — handle this gracefully.

    Returns:
        A non-empty string with outfit suggestions.
        If the wardrobe is empty, offer general styling advice for the item
        rather than raising an exception or returning an empty string.

    TODO:
        1. Check whether wardrobe['items'] is empty.
        2. If empty: call the LLM with a prompt for general styling ideas
           (what kinds of items pair well, what vibe it suits, etc.).
        3. If not empty: format the wardrobe items into a prompt and ask
           the LLM to suggest specific outfit combinations using the new item
           and named pieces from the wardrobe.
        4. Return the LLM's response as a string.

    Before writing code, fill in the Tool 2 section of planning.md.
    """
    # Describe the new item once — reused by both prompt branches.
    item_desc = (
        f"{new_item['title']} ({new_item['category']}, "
        f"{', '.join(new_item['colors'])}; "
        f"style: {', '.join(new_item['style_tags'])})"
    )

    items = wardrobe.get("items", []) if wardrobe else []

    if not items:
        # Empty wardrobe — ask for general styling advice instead of crashing.
        prompt = (
            f"A shopper is considering buying this thrifted item:\n"
            f"{item_desc}\n\n"
            f"They haven't told us what's in their wardrobe yet. Suggest how to "
            f"style this piece in general: what kinds of items pair well with it, "
            f"what vibe or occasions it suits, and 1-2 example outfit ideas. "
            f"Keep it friendly and concise (about 4-6 sentences)."
        )
    else:
        # Format the wardrobe so the LLM can reference pieces by name.
        wardrobe_lines = "\n".join(
            f"- {it['name']} ({it['category']}, {', '.join(it.get('colors', []))})"
            for it in items
        )
        prompt = (
            f"A shopper is considering buying this thrifted item:\n"
            f"{item_desc}\n\n"
            f"Here is what they already own:\n{wardrobe_lines}\n\n"
            f"Suggest 1-2 complete outfits that combine the new item with specific "
            f"pieces from their wardrobe. Refer to the wardrobe pieces by name. "
            f"Briefly explain why each outfit works. Keep it friendly and concise."
        )

    client = _get_groq_client()
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {
                "role": "system",
                "content": (
                    "You are FitFindr, a warm, knowledgeable personal stylist who "
                    "helps people style secondhand fashion finds."
                ),
            },
            {"role": "user", "content": prompt},
        ],
        temperature=0.7,
    )
    return response.choices[0].message.content.strip()


# ── Tool 3: create_fit_card ───────────────────────────────────────────────────

def create_fit_card(outfit: str, new_item: dict) -> str:
    """
    Generate a short, shareable outfit caption for the thrifted find.

    Args:
        outfit:   The outfit suggestion string from suggest_outfit().
        new_item: The listing dict for the thrifted item.

    Returns:
        A 2–4 sentence string usable as an Instagram/TikTok caption.
        If outfit is empty or missing, return a descriptive error message
        string — do NOT raise an exception.

    The caption should:
    - Feel casual and authentic (like a real OOTD post, not a product description)
    - Mention the item name, price, and platform naturally (once each)
    - Capture the outfit vibe in specific terms
    - Sound different each time for different inputs (use higher LLM temperature)

    TODO:
        1. Guard against an empty or whitespace-only outfit string.
        2. Build a prompt that gives the LLM the item details and the outfit,
           and asks for a caption matching the style guidelines above.
        3. Call the LLM and return the response.

    Before writing code, fill in the Tool 3 section of planning.md.
    """
    # 1. Guard against an empty / whitespace-only outfit — return an error
    #    string rather than calling the LLM or raising.
    if not outfit or not outfit.strip():
        return "There was no outfit suggestion, so no caption can be created."

    # 2. Build the caption prompt with the item details and the outfit.
    prompt = (
        f"Write a short, shareable OOTD caption (2-4 sentences) for a thrifted "
        f"find, like a real Instagram or TikTok post — casual and authentic, "
        f"not a product description.\n\n"
        f"Item: {new_item['title']}\n"
        f"Price: ${new_item['price']:.0f}\n"
        f"Platform: {new_item['platform']}\n\n"
        f"Styled outfit:\n{outfit}\n\n"
        f"Mention the item name, the price, and the platform naturally — once "
        f"each. Capture the outfit's vibe in specific terms. Write only the "
        f"caption itself (emojis and hashtags welcome, but keep it tight)."
    )

    # 3. Call the LLM. Higher temperature so captions vary across runs.
    client = _get_groq_client()
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {
                "role": "system",
                "content": (
                    "You are FitFindr, a stylist who writes punchy, authentic "
                    "social-media captions for secondhand fashion finds."
                ),
            },
            {"role": "user", "content": prompt},
        ],
        temperature=1.0,
    )
    return response.choices[0].message.content.strip()
