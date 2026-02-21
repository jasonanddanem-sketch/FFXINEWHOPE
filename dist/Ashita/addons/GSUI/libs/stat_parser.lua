local stat_parser = {}

-- Stat definitions: name, patterns to match, suffix for display
-- Each pattern extracts a numeric value from description/augment text
local stat_defs = {
    -- Casting
    { key = 'fc',          name = 'Fast Cast',         cap = 80,   suffix = '%',  patterns = {'"Fast Cast"%+(%d+)', 'Fast Cast%+(%d+)'} },
    { key = 'qm',          name = 'Quick Magic',       cap = 10,   suffix = '%',  patterns = {'Quick Magic%+(%d+)'} },
    { key = 'conserve_mp', name = 'Conserve MP',       cap = nil,  suffix = '',   patterns = {'"Conserve MP"%+(%d+)', 'Conserve MP%+(%d+)'} },
    { key = 'sird',        name = 'Spell Interrupt',   cap = 100,  suffix = '%',  patterns = {'[Ss]pell [Ii]nterrupt.*%-(%d+)', 'SIRD%+(%d+)'} },
    -- Haste
    { key = 'haste',       name = 'Haste (Gear)',      cap = 26,   suffix = '%',  patterns = {'Haste%+(%d+)'}, exclude = {'Pet'} },
    -- Pet / SMN
    { key = 'bp_delay',    name = 'BP Delay',          cap = nil,  suffix = '',   patterns = {'[Bb]lood [Pp]act.*[Dd]el[aey]*[ .]*%-(%d+)', '[Bb]lood [Pp]act.*[Dd]el[aey]*[ .]*II? %-(%d+)'} },
    { key = 'bp_dmg',      name = 'BP Damage',         cap = nil,  suffix = '',   patterns = {'[Bb]lood [Pp]act [Dd][am]g?%.?%+(%d+)', '[Bb]lood [Pp]act [Dd]amage%+(%d+)'} },
    { key = 'pet_haste',   name = 'Pet: Haste',        cap = nil,  suffix = '%',  patterns = {'Pet: Haste%+(%d+)'} },
    { key = 'pet_atk',     name = 'Pet: Attack',       cap = nil,  suffix = '',   patterns = {'Pet: Attack%+(%d+)', 'Pet: Atk%.%+(%d+)'} },
    { key = 'pet_macc',    name = 'Pet: Mag. Acc.',    cap = nil,  suffix = '',   patterns = {'Pet: Mag%. Acc%.%+(%d+)'} },
    { key = 'pet_mab',     name = 'Pet: MAB',          cap = nil,  suffix = '',   patterns = {'Pet: "Mag%.Atk%.Bns%."%+(%d+)', 'Pet: MAB%+(%d+)'} },
    { key = 'pet_acc',     name = 'Pet: Accuracy',     cap = nil,  suffix = '',   patterns = {'Pet: Acc%.%+(%d+)', 'Pet: Accuracy%+(%d+)'} },
    { key = 'pet_ratk',    name = 'Pet: R.Atk',        cap = nil,  suffix = '',   patterns = {'Pet: R%.Atk%.%+(%d+)'} },
    { key = 'pet_racc',    name = 'Pet: R.Acc',        cap = nil,  suffix = '',   patterns = {'Pet: R%.Acc%.%+(%d+)', 'Pet: Rng%. Acc%.%+(%d+)'} },
    { key = 'perp',        name = 'Avatar Perp.',      cap = nil,  suffix = '',   patterns = {'[Aa]vatar.*[Pp]erpetuation.*%-(%d+)', 'Perpetuation [Cc]ost %-(%d+)'}, negative = true },
    { key = 'summon_skill',name = 'Summoning Skill',   cap = nil,  suffix = '',   patterns = {'[Ss]ummoning [Mm]agic [Ss]kill %+(%d+)', '[Ss]ummoning [Mm]agic%+(%d+)'} },
    -- Melee
    { key = 'da',          name = 'Double Attack',     cap = nil,  suffix = '%',  patterns = {'"Dbl%.Atk%."%+(%d+)', 'Double Attack%+(%d+)', '"Double Attack"%+(%d+)'} },
    { key = 'ta',          name = 'Triple Attack',     cap = nil,  suffix = '%',  patterns = {'"Triple Atk%."%+(%d+)', 'Triple Attack%+(%d+)', '"Triple Attack"%+(%d+)'} },
    { key = 'stp',         name = 'Store TP',          cap = nil,  suffix = '',   patterns = {'"Store TP"%+(%d+)', 'Store TP%+(%d+)'} },
    { key = 'dw',          name = 'Dual Wield',        cap = nil,  suffix = '',   patterns = {'Dual Wield%+(%d+)', '"Dual Wield"%+(%d+)'} },
    { key = 'subtle',      name = 'Subtle Blow',       cap = 50,   suffix = '',   patterns = {'"Subtle Blow"%+(%d+)', 'Subtle Blow%+(%d+)'} },
    { key = 'crit',        name = 'Crit. Hit Rate',    cap = nil,  suffix = '%',  patterns = {'[Cc]ritical [Hh]it [Rr]ate%+(%d+)'} },
    -- WS
    { key = 'ws_dmg',      name = 'WS Damage',         cap = nil,  suffix = '%',  patterns = {'[Ww]eapon [Ss]kill [Dd]amage%+(%d+)', 'WSD%+(%d+)'} },
    -- Magic Offense
    { key = 'mab',         name = 'Magic Atk. Bonus',  cap = nil,  suffix = '',   patterns = {'"Mag%.Atk%.Bns%."%+(%d+)', 'Magic Atk%. Bonus%+(%d+)', 'MAB%+(%d+)'}, exclude = {'Pet'} },
    { key = 'macc',        name = 'Magic Accuracy',    cap = nil,  suffix = '',   patterns = {'Mag%. Acc%.%+(%d+)', 'Magic Accuracy%+(%d+)'}, exclude = {'Pet'} },
    { key = 'mb_dmg',      name = 'Magic Burst Dmg',   cap = 40,   suffix = '%',  patterns = {'[Mm]agic [Bb]urst.*%+(%d+)'} },
    -- Defense
    { key = 'dt',          name = 'Damage Taken',      cap = 50,   suffix = '%',  patterns = {'[Dd]amage [Tt]aken%-(%d+)', 'DT%-(%d+)'}, negative = true, exclude = {'Phys', 'Mag'} },
    { key = 'pdt',         name = 'Phys. Dmg Taken',   cap = 50,   suffix = '%',  patterns = {'[Pp]hys.*[Dd]amage [Tt]aken%-(%d+)', 'PDT%-(%d+)'}, negative = true },
    { key = 'mdt',         name = 'Mag. Dmg Taken',    cap = 50,   suffix = '%',  patterns = {'[Mm]ag.*[Dd]amage [Tt]aken%-(%d+)', 'MDT%-(%d+)'}, negative = true },
    { key = 'meva',        name = 'Magic Evasion',     cap = nil,  suffix = '',   patterns = {'[Mm]ag.*[Ee]va%.?%+(%d+)'} },
    { key = 'mdef',        name = 'Magic Def. Bonus',  cap = nil,  suffix = '',   patterns = {'"Mag%.Def%.Bns%."%+(%d+)', 'Magic Def%. Bonus%+(%d+)'} },
    -- Healing
    { key = 'cure_pot',    name = 'Cure Potency',      cap = 50,   suffix = '%',  patterns = {'"Cure" [Pp]otency%+(%d+)', 'Cure [Pp]otency%+(%d+)'} },
    -- Utility
    { key = 'refresh',     name = 'Refresh',           cap = nil,  suffix = '',   patterns = {'"Refresh"%+(%d+)', 'Refresh%+(%d+)'}, exclude = {'Pet'} },
    { key = 'regen',       name = 'Regen',             cap = nil,  suffix = '',   patterns = {'"Regen"%+(%d+)', 'Regen%+(%d+)'}, exclude = {'Pet'} },
    { key = 'th',          name = 'Treasure Hunter',   cap = nil,  suffix = '',   patterns = {'"Treasure Hunter"%+(%d+)', 'Treasure Hunter%+(%d+)'} },
    -- Stats
    { key = 'str',         name = 'STR',               cap = nil,  suffix = '',   patterns = {'STR%+(%d+)'}, exclude = {'Pet'} },
    { key = 'dex',         name = 'DEX',               cap = nil,  suffix = '',   patterns = {'DEX%+(%d+)'}, exclude = {'Pet'} },
    { key = 'vit',         name = 'VIT',               cap = nil,  suffix = '',   patterns = {'VIT%+(%d+)'}, exclude = {'Pet'} },
    { key = 'agi',         name = 'AGI',               cap = nil,  suffix = '',   patterns = {'AGI%+(%d+)'}, exclude = {'Pet'} },
    { key = 'int',         name = 'INT',               cap = nil,  suffix = '',   patterns = {'INT%+(%d+)'}, exclude = {'Pet'} },
    { key = 'mnd',         name = 'MND',               cap = nil,  suffix = '',   patterns = {'MND%+(%d+)'}, exclude = {'Pet'} },
    { key = 'chr',         name = 'CHR',               cap = nil,  suffix = '',   patterns = {'CHR%+(%d+)'}, exclude = {'Pet'} },
    { key = 'hp',          name = 'HP',                cap = nil,  suffix = '',   patterns = {'HP%+(%d+)'} },
    { key = 'mp',          name = 'MP',                cap = nil,  suffix = '',   patterns = {'MP%+(%d+)'} },
    { key = 'acc',         name = 'Accuracy',          cap = nil,  suffix = '',   patterns = {'Accuracy%+(%d+)'}, exclude = {'Pet', 'Rng', 'Mag'} },
    { key = 'atk',         name = 'Attack',            cap = nil,  suffix = '',   patterns = {'Attack%+(%d+)'}, exclude = {'Pet', 'Rng', 'Mag'} },
}

-- Extract a numeric value from a text line using patterns
local function extract_value(text, patterns, exclude)
    if not text then return 0 end
    -- Check exclusions: skip this line if it contains an excluded prefix
    if exclude then
        for _, ex in ipairs(exclude) do
            -- Check if the exclude word appears right before the match context
            -- We do a simple check: if the line contains "Pet:" and we're excluding Pet, skip
            if text:find(ex) then return 0 end
        end
    end
    for _, pat in ipairs(patterns) do
        local val = text:match(pat)
        if val then return tonumber(val) or 0 end
    end
    return 0
end

-- Parse a single item (description + augments) and return stat contributions
local function parse_item_stats(item)
    local stats = {}
    if not item then return stats end

    -- Gather all text lines to scan
    local lines = {}
    if item.description then
        for line in item.description:gmatch('[^\r\n]+') do
            table.insert(lines, line)
        end
    end
    if item.augments then
        for _, aug in ipairs(item.augments) do
            table.insert(lines, aug)
        end
    end

    for _, def in ipairs(stat_defs) do
        local total = 0
        for _, line in ipairs(lines) do
            total = total + extract_value(line, def.patterns, def.exclude)
        end
        if total > 0 then
            stats[def.key] = total
        end
    end

    return stats
end

-- Calculate totals from all equipped items
-- equipment_data: table of slot_name -> { item = item_info }
function stat_parser.calc_totals(equipment_data)
    local totals = {}
    for _, def in ipairs(stat_defs) do
        totals[def.key] = 0
    end

    if not equipment_data then return totals end

    for slot_name, eq_data in pairs(equipment_data) do
        if eq_data and eq_data.item then
            local item_stats = parse_item_stats(eq_data.item)
            for key, val in pairs(item_stats) do
                totals[key] = (totals[key] or 0) + val
            end
        end
    end

    return totals
end

-- Get ordered list of stats that have non-zero values, for display
function stat_parser.get_display_stats(totals)
    local result = {}
    for _, def in ipairs(stat_defs) do
        local val = totals[def.key] or 0
        if val > 0 then
            local display_val = def.negative and ('-' .. val) or ('+' .. val)
            local cap_text = ''
            if def.cap then
                if val >= def.cap then
                    cap_text = ' [CAPPED]'
                else
                    cap_text = ' /' .. def.cap
                end
            end
            table.insert(result, {
                key = def.key,
                name = def.name,
                value = val,
                display = def.name .. ': ' .. display_val .. def.suffix .. cap_text,
                capped = def.cap and val >= def.cap or false,
                category = get_category(def.key),
            })
        end
    end
    return result
end

-- Category grouping for display
function get_category(key)
    local categories = {
        fc = 'Casting', qm = 'Casting', conserve_mp = 'Casting', sird = 'Casting',
        haste = 'Haste',
        bp_delay = 'Pet/SMN', bp_dmg = 'Pet/SMN', pet_haste = 'Pet/SMN',
        pet_atk = 'Pet/SMN', pet_macc = 'Pet/SMN', pet_mab = 'Pet/SMN',
        pet_acc = 'Pet/SMN', pet_ratk = 'Pet/SMN', pet_racc = 'Pet/SMN',
        perp = 'Pet/SMN', summon_skill = 'Pet/SMN',
        da = 'Melee', ta = 'Melee', stp = 'Melee', dw = 'Melee',
        subtle = 'Melee', crit = 'Melee', acc = 'Melee', atk = 'Melee',
        ws_dmg = 'WS',
        mab = 'Magic', macc = 'Magic', mb_dmg = 'Magic',
        dt = 'Defense', pdt = 'Defense', mdt = 'Defense',
        meva = 'Defense', mdef = 'Defense',
        cure_pot = 'Healing',
        refresh = 'Utility', regen = 'Utility', th = 'Utility',
        str = 'Stats', dex = 'Stats', vit = 'Stats', agi = 'Stats',
        int = 'Stats', mnd = 'Stats', chr = 'Stats',
        hp = 'Stats', mp = 'Stats',
    }
    return categories[key] or 'Other'
end

-- Format stats as a multi-line string grouped by category
function stat_parser.format_summary(totals)
    local display = stat_parser.get_display_stats(totals)
    if #display == 0 then return 'No stats detected.\nEquip gear to see totals.' end

    -- Group by category
    local groups = {}
    local group_order = { 'Casting', 'Haste', 'Pet/SMN', 'Melee', 'WS', 'Magic', 'Defense', 'Healing', 'Utility', 'Stats' }
    for _, cat in ipairs(group_order) do
        groups[cat] = {}
    end

    for _, stat in ipairs(display) do
        local cat = stat.category
        if not groups[cat] then groups[cat] = {} end
        table.insert(groups[cat], stat)
    end

    local lines = {}
    for _, cat in ipairs(group_order) do
        local items = groups[cat]
        if items and #items > 0 then
            table.insert(lines, '-- ' .. cat .. ' --')
            for _, stat in ipairs(items) do
                table.insert(lines, stat.display)
            end
            table.insert(lines, '')
        end
    end

    return table.concat(lines, '\n')
end

return stat_parser
