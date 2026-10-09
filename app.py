import re
import html
import streamlit as st

st.set_page_config(page_title="ChapterClarity", page_icon="📖", layout="wide")

st.markdown("""
<style>
.block-container {max-width: 1000px; padding-top: 2rem;}
.hero {padding: 1.5rem; border-radius: 16px; background: linear-gradient(120deg,#eef2ff,#f0fdfa); margin-bottom: 1rem;}
.hero h1 {margin:0; color:#172554;}
.hero p {color:#334155; margin-bottom:0;}
.sentence {padding: 10px 12px; border-radius: 8px; margin: 7px 0; line-height: 1.6;}
.hard {background:#fff0e8 !important; color:#7c2d12 !important; border-left:4px solid #ea580c;}
.normal {background:#f8fafc !important; color:#1e293b !important; border-left:4px solid #cbd5e1;}
.small-note {color:#94a3b8; font-size:0.9rem;}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="hero">
<h1>📖 ChapterClarity</h1>
<p>A free, quick readability check for writers, students, and editors.</p>
</div>
""", unsafe_allow_html=True)

st.write("Paste a chapter below to estimate its readability and find the five sentences that may be hardest for readers.")
chapter = st.text_area("Your chapter", height=260, placeholder="Paste your chapter here…")
col1, col2 = st.columns([1, 1])
with col1:
    audience = st.selectbox("Intended audience", ["General readers", "Middle school", "High school", "University / specialist"])
with col2:
    st.caption("Your text is analyzed in this session. This demo does not save chapters.")

def words(text):
    return re.findall(r"\b[\w]+(?:['’-][\w]+)*\b", text)

def clean_chapter(text):
    """Remove a likely standalone title line from the readability analysis."""
    lines = [line.strip() for line in text.strip().splitlines() if line.strip()]
    if len(lines) >= 2:
        first = lines[0]
        # A short first line without sentence-ending punctuation is likely a title.
        if len(words(first)) <= 12 and not re.search(r"[.!?]$", first):
            return "\n".join(lines[1:]), first
    return text.strip(), None

def split_sentences(text):
    # Join line breaks, then split after sentence-ending punctuation.
    normalized = re.sub(r"\s+", " ", text.strip())
    if not normalized:
        return []
    parts = re.split(r'(?<=[.!?])\s+(?=["“‘\'(\[]?[A-Z0-9])', normalized)
    return [part.strip() for part in parts if part.strip() and words(part)]

def syllables(word):
    word = re.sub(r"[^a-z]", "", word.lower())
    if not word:
        return 1
    if len(word) <= 3:
        return 1
    groups = re.findall(r"[aeiouy]+", word)
    count = len(groups)
    if word.endswith("e") and count > 1 and not word.endswith(("le", "ye")):
        count -= 1
    if word.endswith("es") and count > 1 and not word.endswith(("ses", "zes")):
        count -= 1
    return max(1, count)

def sentence_difficulty(sentence):
    ws = words(sentence)
    if not ws:
        return 0
    long_words = sum(1 for w in ws if len(re.sub(r"[^A-Za-z]", "", w)) >= 9)
    syllable_count = sum(syllables(w) for w in ws)
    return round((len(ws) * 0.7) + (long_words * 1.8) + (syllable_count / len(ws) * 2.0), 2)

def flesch_reading_ease(text, sentences):
    ws = words(text)
    if not ws or not sentences:
        return None
    syllable_count = sum(syllables(w) for w in ws)
    words_per_sentence = len(ws) / len(sentences)
    syllables_per_word = syllable_count / len(ws)
    return round(206.835 - 1.015 * words_per_sentence - 84.6 * syllables_per_word, 1)

if st.button("Analyze chapter", type="primary", use_container_width=True):
    if len(chapter.strip()) < 30:
        st.warning("Please paste a longer passage (at least a few sentences) for a more useful estimate.")
    else:
        analysis_text, title = clean_chapter(chapter)
        sentences = split_sentences(analysis_text)
        all_words = words(analysis_text)
        score = flesch_reading_ease(analysis_text, sentences)
        avg_words = round(len(all_words) / max(1, len(sentences)), 1) if sentences else 0

        if not sentences or not all_words:
            st.warning("We couldn't detect enough sentences. Please check punctuation and try again.")
            st.stop()

        difficult = sorted(enumerate(sentences), key=lambda item: sentence_difficulty(item[1]), reverse=True)[:5]
        difficult_indices = {idx for idx, _ in difficult}

        m1, m2, m3 = st.columns(3)
        m1.metric("Readability score", f"{score}/100" if score is not None else "N/A")
        m2.metric("Words", f"{len(all_words):,}")
        m3.metric("Sentences", f"{len(sentences):,}")

        if title:
            st.caption(f"Detected and excluded title: {title}")

        if score is not None:
            if score >= 70:
                interpretation = "Generally easy to read"
            elif score >= 50:
                interpretation = "Moderately difficult"
            elif score >= 30:
                interpretation = "Difficult"
            else:
                interpretation = "Very difficult"
            st.info(f"**Estimated reading level:** {interpretation}. Average sentence length: {avg_words} words. Audience selected: {audience}.")

        st.subheader("Your chapter, with the five hardest sentences highlighted")
        rendered = []
        for i, sentence in enumerate(sentences):
            cls = "hard" if i in difficult_indices else "normal"
            marker = " ⚠️" if i in difficult_indices else ""
            rendered.append(f'<div class="sentence {cls}">{html.escape(sentence)}{marker}</div>')
        st.markdown("".join(rendered), unsafe_allow_html=True)

        st.subheader("Five sentences to review")
        for rank, (idx, sentence) in enumerate(difficult, 1):
            st.markdown(f"**{rank}. Sentence {idx+1} · difficulty estimate {sentence_difficulty(sentence)}**")
            st.write(sentence)
            ws = words(sentence)
            reasons = []
            if len(ws) >= 25:
                reasons.append("long sentence")
            if any(len(re.sub(r"[^A-Za-z]", "", w)) >= 9 for w in ws):
                reasons.append("several long words")
            if not reasons:
                reasons.append("combined length and syllable complexity")
            st.caption("Review signal: " + ", ".join(reasons) + ". Consider splitting the sentence or replacing unnecessary complex words.")

        st.caption("Limitations: this is a heuristic estimate, not an editorial judgment. Abbreviations, dialogue, names, technical terms, and sentence splitting can affect the score. Always review the highlights yourself.")

st.divider()
st.markdown('<p class="small-note">ChapterClarity is a lightweight writing aid. A high or low score is only a guide; the author decides what is clear for their audience.</p>', unsafe_allow_html=True)
