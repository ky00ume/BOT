# Churider Existing Content Migration Map

Current branch audit. Purpose: preserve the existing game while routing meaningful actions through World → Event → Memory and enforcing player agency.

## Legend
- CONNECTED: already emits/uses the new core in a meaningful path.
- PARTIAL: some path is connected, but state/lifecycle/memory is still legacy.
- LEGACY: existing feature works outside the new core.
- PROTECTED: player choice must remain explicit; the world must not decide it.

## Content map

| Area | Current | Agency | Evidence / migration target |
|---|---|---|---|
| Care room / petting | CONNECTED | DIRECTED | `social_cog`, care UI → care events, bond/traits/pet observation. Keep shared bond; suspicious Lily is flavour only. |
| Feeding / playing | CONNECTED | DIRECTED | care UI emits care events and feeds memory/bond/traits. |
| Fishing | CONNECTED | DIRECTED | persistent Activity start/finish + bond/habit. Still needs restart reconciliation. |
| Movement | PARTIAL | DIRECTED | `/이동` emits `world.moved`, but movement state mutation is still legacy and not atomic with event append. |
| Battle | PARTIAL | PLAYER_CONTROLLED | battle cog emits battle events, but HP/MP/rewards/items mutate directly in `battle.py`; auto-potion spends inventory during battle. Needs explicit policy + transaction boundary. |
| World Clock / ordinary idle life | CONNECTED | AUTONOMOUS | autonomous low-stakes world events exist and are suppressed while an Activity is current. |
| Diary / memory | CONNECTED | projection | event-backed diary selects distinct meaningful beats; legacy fallback remains for compatibility. |
| Traits / habits / personality | CONNECTED | projection | derived from event history; currently bounded recent-event projection, not durable trait state. |
| Gathering / mining / woodcut | LEGACY | DIRECTED | direct energy/item/skill mutation in `gathering.py`; wrap as Activity + completion event. Do not auto-start. |
| Crafting / metallurgy / potion / cooking | LEGACY | DIRECTED + resource protection | recipe/material mutation is direct. Player chooses recipe/resources; rare resources must never be auto-spent. |
| Rest | LEGACY | AUTONOMOUS-capable | current command runs a timed RestEngine and explicitly allows other activities. Needs one concurrency policy before Activity migration. World may initiate ordinary rest, but player command remains valid. |
| Adventure / exploration | LEGACY | PLAYER_CONTROLLED | many direct gold/item/HP/energy effects and encounter choices. Treat encounters as world opportunities; choices remain player-owned. |
| Normal quests | LEGACY | PLAYER_CONTROLLED | accept/complete mutate via QuestManager and save. Add quest events after explicit player decisions. |
| Story quests / story exploration | LEGACY + PROTECTED | PLAYER_CONTROLLED | large scripted choice/cutscene/battle surface. Never auto-advance consequential story decisions. |
| NPC conversation / affinity | LEGACY + PROTECTED | PLAYER_CONTROLLED | conversation and relationship changes are legacy. Ordinary NPC presence may be world-driven; dialogue choices/relationship commitments stay player-owned. |
| Raphael contract | LEGACY + PROTECTED | FORBIDDEN_AUTONOMY | accept/reject/complete are explicit commands. Never world-decide a contract. |
| Jobs (`/알바`) | LEGACY | DIRECTED | async job flow; natural Activity candidate with due/finish event. |
| Equipment / costume / titles | LEGACY + PROTECTED | PLAYER_CONTROLLED | explicit inventory/loadout identity choices; do not autonomously equip/swap. |
| Inventory / storage / discard | LEGACY + PROTECTED | PLAYER_CONTROLLED | resource ownership operations. Discard/upgrade/storage moves require player action. |
| Economy / shop / restaurant / gacha | LEGACY + PROTECTED | PLAYER_CONTROLLED | spending paths remain legacy. Purchases/gacha/valuable spend must never be autonomous. |
| Training / skills | LEGACY | DIRECTED | progression mutation is legacy; explicit training can become Activity/event. Passive skill gains caused by a player-controlled action can remain consequences. |
| Achievements / collection / rankings | LEGACY | projection | mostly read/projection/reward surfaces. Consume domain events rather than becoming authoritative action paths. |
| Music / composition | LEGACY | PLAYER_CONTROLLED | creative/player-authored content; preserve direct authorship. Events may remember completion, never generate the choice for them. |
| Bulletin / town notice / weather / village status | LEGACY | WORLD/READ | mostly world/read surfaces. Good event consumers; avoid forcing them into Activity when no stateful action occurs. |
| Special NPC encounters | LEGACY + PROTECTED | mixed | world may surface an encounter; keyword/dialogue/contract/reward decisions remain player-owned. |

## Migration waves

### Wave A — lifecycle first
1. Restart reconciliation for Fishing Activity.
2. Jobs, gathering, woodcut/mining: Directed Activity start → due/finish → event.
3. Decide Rest concurrency semantics, then make ordinary rest restart-safe.

### Wave B — authoritative consequences
1. Introduce a small transaction / Unit-of-Work boundary for state mutation + event append.
2. Move movement through it first (smallest stateful slice).
3. Move battle reward/HP/item settlement through it without changing combat choices.
4. Move crafting/resource settlement through it; enforce rare-resource protection.

### Wave C — narrative/player-owned systems
1. Quest accepted/completed events after explicit commands.
2. Adventure encounter offered/resolved events; world may offer, never choose.
3. Story and NPC relationship events only after player choice.
4. Contracts remain FORBIDDEN_AUTONOMY end-to-end.

### Wave D — projections
Achievements, collection, diary, traits, village/bulletin surfaces consume the richer event stream. Avoid duplicate authoritative state where an event projection is enough.

## Red flags found during audit
- Battle contains auto-potion inventory spending. This predates the new agency contract and needs an explicit design decision; do not silently broaden it to other resources.
- Rest currently says other activities can continue during rest, while the new Activity service models one shared current activity. Do not migrate Rest until concurrency semantics are explicit.
- Movement and battle append events outside the legacy mutation transaction, so state/event divergence is possible on failure.
- Traits are currently derived from a bounded recent event window, so an old trait can disappear as history rolls forward.
- `shared_player`-style mutable state remains throughout legacy engines; migrate by vertical slice, not a global rewrite.

## Definition of migrated
A stateful content path is migrated only when: player agency classification is enforced; lifecycle survives/reconciles restart when time-based; state mutation and event recording have one success boundary; Memory can consume the event without inventing facts; legacy UI/gameplay remains usable unless intentionally redesigned.
