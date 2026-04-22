def wrap_text(text, font, max_width):
    """
    Splits text into a list of lines that fit within max_width when rendered.
    """
    words = []
    if text is not None:
        words = text.split(' ')
    lines = []
    current_line = []
    for word in words:
        # Check if adding the next word exceeds max_width
        if font.size(' '.join(current_line + [word]))[0] < max_width and not "\n" in word:
            current_line.append(word)
        else:
            if "\n" in word:
                new_string = word.replace("\n", " ")                
                new_words = new_string.split(' ')
                if font.size(' '.join(current_line + [new_words[0]]))[0] < max_width:
                    current_line.append(new_words[0])
                    lines.append(' '.join(current_line))
                    current_line = [new_words[-1]]
                else:
                    lines.append(' '.join(current_line))
                    lines.append(new_words[0])
                    current_line = [new_words[-1]]
            else:
                # If current_line is empty, the word itself is too long for one line.
                # In this simple implementation, we'll just put it on its own line.
                # A more robust solution might hyphenate or truncate.
                if not current_line:
                    lines.append(word)
                else:
                    lines.append(' '.join(current_line))
                    current_line = [word]
    
    if current_line:
        lines.append(' '.join(current_line))
    return lines