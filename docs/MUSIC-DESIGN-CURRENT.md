# Music Design — Current

## Rhythm difficulty contract

All playable songs expose four authored charts. Difficulty is not produced by merely scaling note count.

- EASY — melody-first; roughly 70–80% of the lead line, almost no chords, minimal SPACE.
- NORMAL — full melody + important accompaniment accents; 2-key chords and simple SPACE holds begin.
- HARD — main authored play experience; melody + accompaniment, 2–3 key chords, crossing patterns, simultaneous SPACE holds/releases.
- HADES — song-specific virtuoso interpretation; trills, stair patterns, hand alternation, pedal overlap, and sectional bursts only where musically justified.

Level scale is 1–30. A song's HADES chart does not have to be near 30; the ceiling follows the song.

## Location BGM contract

Location BGM is designed for indefinite looping: no strong intro/outro, no terminal cadence, stable emotional temperature, cyclical form. Generated masters are post-processed into loop assets before placement.

Initial routing:
- 비전의 탑 → `bgm/locations/tower`
- 마이코니드 군락 → `bgm/locations/myconid_colony`
- 비전의 탑 ↔ 마이코니드 군락 생활 이동로 → `bgm/locations/colony_road`
- 드레드 할로우 사냥터 상세 화면 → `bgm/locations/hunting_ground` (첫 사냥터 배치; 다른 사냥터는 추후 개별곡)

Discord voice remains opt-in through `/소리 켜기`. When enabled, opening/moving between these scenes switches BGM automatically. Short interrupting sound cues resume the current BGM when they finish.
