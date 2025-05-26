# Speech Text File Format

Speech text files are stored in JSON format. Each file represents a single piece of text to be memorized.

## Structure

The JSON file should contain a single object with the following fields:

-   `title` (String, Mandatory): The title of the speech or text.
-   `text` (String, Mandatory): The full content of the speech or text. Newlines can be included using `\n`.
-   `time_limit` (Integer, Optional): An optional time limit for memorizing or reciting the text, in seconds.
-   `description` (String, Optional): An optional brief description of the text.
-   `tags` (List of Strings, Optional): An optional list of tags for categorizing the text.

## Example

```json
{
  "title": "Example Speech",
  "text": "This is the first line of the speech.\nThis is the second line.",
  "time_limit": 120,
  "description": "A short example speech for demonstration purposes.",
  "tags": ["example", "demo"]
}
```
