class TextFormatter:
    @staticmethod
    def split_into_threads(text, limit=270):
        if not text: return []
        if len(text) <= limit: return [text]

        threads = []
        while len(text) > limit:
            split_index = text.rfind(' ', 0, limit)
            if split_index == -1: split_index = limit
            threads.append(text[:split_index])
            text = text[split_index:].strip()
        
        if text: threads.append(text)
        return [f"{t} ({i+1}/{len(threads)})" for i, t in enumerate(threads)]