# USSD Flow

This document maps the complete menu tree implemented in `app.py`, derived from
`ussd_callback()` and the screen renderer functions.

## How to read this

- **`level`** = number of resolved inputs (`len(inputs)`), *after* `resolve_path()`
  has consumed any `0` (back) / `00` (home) tokens.
- **`inputs[n]`** = the value at each position of the resolved path.
- **CON** = session continues (menu shown). **END** = session terminates.
- Because `0`/`00` are consumed before routing, they are shown as global
  navigation, not per-screen edges — they simply shorten the path and re-render
  an earlier screen.

## Branch keys

| Position | Meaning |
|----------|---------|
| `inputs[0]` | Farm key (`1` Kiambu Kikuy, `2` Sunright) |
| `inputs[1]` | Farm menu choice (`1` Advisories, `2` Manage Crops) |
| `inputs[2]` | Advisory index **or** crop index / Add-Crop sentinel |
| `inputs[3]` | `1` See steps (advisories) **or** crop action / category key |
| `inputs[4]` | Crop-in-category index **or** crop-specific advisory index |
| `inputs[5]` | `1` See steps (crop-specific advisory) |

> **Note — dynamic "Add Crop" option:** in the Manage Crops branch, the sentinel
> `add_option = str(len(crops) + 1)`. For Kiambu (3 crops) it is `4`; for Sunright
> (2 crops) it is `3`. The same digit routes differently per farm.

## Top-level routing

```mermaid
flowchart TD
    start(["POST /ussd"]) --> resolve["resolve_path(text.split('*'))<br/>0=back · 00=home"]
    resolve --> L0{"level == 0?"}
    L0 -->|yes| home["CON farm_list_screen<br/>1. Kiambu Kikuy · 2. Sunright"]
    L0 -->|no| farmlookup{"FARMS.get(inputs[0])"}
    farmlookup -->|miss| invalid["END Invalid selection"]
    farmlookup -->|hit| L1{"level == 1?"}
    L1 -->|yes| menu["CON farm_menu_screen<br/>1. See Advisories · 2. Manage Crops"]
    L1 -->|no| branch{"inputs[1]"}
    branch -->|"1"| adv(["Advisories branch"])
    branch -->|"2"| crops(["Manage Crops branch"])
    branch -->|other| fallthrough["END Invalid option"]
```

## Advisories branch — `inputs[1] == "1"`

```mermaid
flowchart TD
    a2{"level == 2"} -->|yes| list["CON advisories_list_screen<br/>numbered list, severity tags"]
    a3{"level == 3"} -->|"inputs[2] = adv index"| detail["CON advisory_detail_screen<br/>title + 120-char desc<br/>1. See action steps"]
    a3 -->|bad index| ai3["END Invalid selection"]
    a4{"level == 4 and inputs[3] == '1'"} -->|yes| steps["CON advisory_steps_screen<br/>numbered steps + valid_days"]
    a4 -->|bad index| ai4["END Invalid selection"]

    list --> a3
    detail --> a4
```

## Manage Crops branch — `inputs[1] == "2"`

`add_option = str(len(crops) + 1)` is the "Add Crop" sentinel at `inputs[2]`.

```mermaid
flowchart TD
    c2{"level == 2"} -->|yes| clist["CON crops_list_screen<br/>crops + 'Add Crop' option"]

    c2 --> c3{"level == 3"}
    c3 -->|"inputs[2] == add_option"| cat["CON add_crop_category_screen<br/>7 categories"]
    c3 -->|"inputs[2] = crop index"| manage["CON crop_manage_screen<br/>1. Remove · 2. View advisories"]
    c3 -->|bad index| ci3["END Invalid selection"]

    c3 --> c4{"level == 4"}
    c4 -->|"add path: inputs[3]=category"| catsel["CON add_crop_select_screen<br/>5 crops in category"]
    c4 -->|"add path: bad category"| cic["END Invalid category"]
    c4 -->|"manage path: inputs[3]=='1'"| removed["END crop_removed_screen"]
    c4 -->|"manage path: inputs[3]=='2'"| cadv["CON crop_advisories_screen<br/>advisories filtered by crop"]
    c4 -->|"manage path: other"| ci4["END Invalid option"]

    c4 --> c5add{"level == 5 and inputs[2]==add_option"}
    c5add -->|"inputs[4]=crop in category"| added["END crop_added_screen"]
    c5add -->|bad index/category| ci5a["END Invalid selection / category"]

    c4 --> c5adv{"level == 5 and inputs[3]=='2'"}
    c5adv -->|"inputs[4]=adv index"| cdetail["CON advisory_detail_screen"]
    c5adv -->|bad index| ci5b["END Invalid selection"]

    c5adv --> c6{"level == 6 and inputs[3]=='2' and inputs[5]=='1'"}
    c6 -->|yes| csteps["CON advisory_steps_screen"]
    c6 -->|bad index| ci6["END Invalid selection"]
```

## Path examples

| Resolved `text` | Screen reached |
|-----------------|----------------|
| *(empty)* | Farm list (home) |
| `1` | Kiambu farm menu |
| `1*1` | Kiambu advisories list |
| `1*1*3` | 3rd advisory detail |
| `1*1*3*1` | 3rd advisory action steps |
| `1*2` | Kiambu crops list |
| `1*2*4` | Add Crop → category list (Kiambu: `add_option == 4`) |
| `1*2*4*5*1` | Added "Avocado" (Fruits → first crop) — `END` |
| `1*2*1*1` | Removed crop #1 — `END` |
| `1*2*1*2*1*1` | Crop #1 → its advisories → 1st advisory → steps |
| `1*1*0` | Back from advisories list → Kiambu farm menu |
| `1*1*3*00` | Home from advisory detail → farm list |

