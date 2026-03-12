# ... 保持之前的代码不变，直接从 Tab 4 开始替换 ...

# --------- 标签 4: 经文 ---------
with tabs[3]:
    st.markdown('<div class="verse-card" style="text-align: left; line-height: 2.0; font-size: 1.1rem;">', unsafe_allow_html=True)
    
    st.markdown("### 🎧 聆听经文")
    # 恢复两列布局，因为调速框被移到了底层的播放器内部
    col1, col2 = st.columns([2, 1])
    voice_choice = col1.selectbox("选择朗读声音", ["温和女声", "沉稳男声", "清脆童声"], label_visibility="collapsed")
    
    if col2.button("加载/播放朗读"):
        if not st.secrets.get("GCP_API_KEY") and not GEMINI_KEY:
            st.error("请在 Secrets 中配置 API_KEY 以启用朗读功能。")
        else:
            combined_text = "".join(FULL_TEXT_ORIGINAL)
            audio_b64 = get_cached_tts(voice_choice, combined_text)
            
            if audio_b64:
                wrapped_text_html = ""
                for para in FULL_TEXT_DISPLAY:
                    if para.strip():
                        wrapped_text_html += "<p>"
                        for char in para:
                            display_char = "&nbsp;&nbsp;" if char == " " else char
                            wrapped_text_html += f"<span class='tts-char'>{display_char}</span>"
                        wrapped_text_html += "</p>"

                # 核心升级：在 HTML 中原生注入速度控制下拉框和对应的 JS 监听器
                sync_html = f"""
                <style>
                    .player-wrapper {{ background: #fcfaf7; padding: 15px; border-radius: 8px; border: 1px solid #f5f0e6; margin-bottom: 20px; display: flex; flex-direction: column; gap: 10px; }}
                    .controls-row {{ display: flex; justify-content: flex-end; align-items: center; gap: 10px; }}
                    audio {{ width: 100%; outline: none; border-radius: 8px; }}
                    select {{ padding: 6px 12px; border-radius: 6px; border: 1px solid #d6cbb8; background: #fff; color: #4a3f31; font-family: 'Noto Serif SC', serif; cursor: pointer; outline: none; }}
                    .tts-text-box {{ font-family: 'Noto Serif SC', serif; font-size: 1.15rem; line-height: 2.0; color: #4a3f31; padding: 10px; word-break: break-all; }}
                    .tts-char {{ transition: color 0.1s; display: inline-block; }}
                    .highlighted {{ color: #d84315; font-weight: bold; background-color: #fbe9e7; border-radius: 2px; }}
                </style>
                
                <div class="player-wrapper">
                    <div class="controls-row">
                        <span style="color: #6b5c4a; font-size: 0.9rem;">实时播放速度:</span>
                        <select id="speed-selector">
                            <option value="1.0">1.0x (原速)</option>
                            <option value="1.25">1.25x (舒缓)</option>
                            <option value="1.5">1.5x (轻快)</option>
                            <option value="2.0">2.0x (极速)</option>
                        </select>
                    </div>
                    <audio id="audio-player" controls autoplay src="data:audio/mp3;base64,{audio_b64}"></audio>
                </div>
                
                <div class="tts-text-box" id="text-container">
                    {wrapped_text_html}
                </div>
                
                <script>
                    const audio = document.getElementById('audio-player');
                    const speedSelector = document.getElementById('speed-selector');
                    const spans = document.querySelectorAll('.tts-char');
                    const totalChars = spans.length;

                    // 监听下拉框变化，实时无缝调整音频速度
                    speedSelector.addEventListener('change', (e) => {{
                        audio.playbackRate = parseFloat(e.target.value);
                    }});

                    // 监听播放进度，同步文字高亮
                    audio.addEventListener('timeupdate', () => {{
                        if (audio.duration) {{
                            const progress = audio.currentTime / audio.duration;
                            const targetIndex = Math.floor(progress * totalChars);

                            spans.forEach((span, index) => {{
                                if (index <= targetIndex) {{
                                    span.classList.add('highlighted');
                                }} else {{
                                    span.classList.remove('highlighted');
                                }}
                            }});
                        }}
                    }});
                </script>
                """
                components.html(sync_html, height=800, scrolling=True)
    else:
        st.markdown("---")
        for para in FULL_TEXT_DISPLAY:
            if para.strip():
                st.markdown(f"{para}  ")
                
    st.markdown('</div>', unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #a69986; margin-top: 2rem;'>愿以此功德，普及于一切。</p>", unsafe_allow_html=True)