local set_generator = {}

local selected_items = {}

local slot_order = {
    'main', 'sub', 'range', 'ammo',
    'head', 'neck', 'left_ear', 'right_ear',
    'body', 'hands', 'left_ring', 'right_ring',
    'back', 'waist', 'legs', 'feet',
}

function set_generator.clear()
    selected_items = {}
end

function set_generator.set_slot(slot_name, item_info)
    selected_items[slot_name] = item_info
end

function set_generator.remove_slot(slot_name)
    selected_items[slot_name] = nil
end

function set_generator.get_slot(slot_name)
    return selected_items[slot_name]
end

function set_generator.get_all_slots()
    return selected_items
end

function set_generator.has_items()
    for _ in pairs(selected_items) do
        return true
    end
    return false
end

function set_generator.populate_from_equipment(equipment_data)
    set_generator.clear()
    for slot_name, slot_data in pairs(equipment_data) do
        if slot_data.item then
            selected_items[slot_name] = slot_data.item
        end
    end
end

local function format_augments(augments)
    if not augments or #augments == 0 then return nil end
    local parts = {}
    for _, aug in ipairs(augments) do
        local escaped = aug:gsub("'", "\\'")
        table.insert(parts, "'" .. escaped .. "'")
    end
    return '{' .. table.concat(parts, ',') .. '}'
end

local function format_entry(item_info)
    local name = item_info.name
    local augs = format_augments(item_info.augments)
    if augs then
        return '{ name="' .. name .. '", augments=' .. augs .. ' }'
    else
        return '"' .. name .. '"'
    end
end

function set_generator.generate()
    local lines = {}
    table.insert(lines, '{')

    for _, slot_name in ipairs(slot_order) do
        local item = selected_items[slot_name]
        if item then
            table.insert(lines, '        ' .. slot_name .. '=' .. format_entry(item) .. ',')
        end
    end

    table.insert(lines, '}')
    return table.concat(lines, '\n')
end

function set_generator.generate_to_clipboard()
    local output = set_generator.generate()
    windower.copy_to_clipboard(output)
    return output
end

function set_generator.generate_to_file(filename)
    local output = set_generator.generate()
    local path = windower.addon_path .. 'data/'
    if not windower.dir_exists(path) then
        windower.create_dir(path)
    end
    local f = io.open(path .. (filename or 'generated_set') .. '.lua', 'w+')
    if f then
        f:write(output)
        f:close()
        return true, path .. (filename or 'generated_set') .. '.lua'
    end
    return false
end

return set_generator
