local function sdx_dl_hint_func(arg_index, word, word_index, line_state, user_data)
    local hint
    local end_line = line_state:getword(word_index - 1)
    if end_line == 'sdx-dl' then
      hint = "Expected for 'sdx-dl': search terms/filename/path, flags/config"
    end
    return hint
end

-- Arguments options
local options = clink.argmatcher():addarg('quiet', 'verbose', 'force', 'no_choose', 'no_filter', 'nlines', 'path',
'proxy', 'Season', 'imdb', 'SubX')

-- Files options
local fileopts = {"-p", "--path"}

-- App argument matcher
clink.argmatcher("sdx-dl")

-- Arguments flags
:addflags("-p", "-h", "-q", "-v", "-nc", "-nf", "-S", "-i", "-f", "-V", "-cv", "-k", "-t", "-i", "-sx",
"-vc", "-sc", "-lc", "-c", "-r", "-b", "-cb")

:addflags("--path", "--help", "--quiet","--verbose", "--no-choose", "--no-filter", "--num-lines", "--proxy",
"--Season", "--imdb", "--force", "--version", "--check-version", "--keyword", "--title", "--view-config",
"--save-config", "--load-config", "--config", "--reset", "--bypass", "--conf-bypass")

-- Arguments with flags matcher
:addflags({"--proxy", "-x"}..clink.argmatcher():addarg("http://", "https://"))
:addflags({"--nlines", "-nl"}..clink.argmatcher():addarg("5", "10", "15", "20"))
:addflags({"--bypass", "-b"}..clink.argmatcher():addarg("force", "manual"))
:addflags("-c"..options)
:addflags("-r"..options)
:addflags("--config"..options)
:addflags("--reset"..options)
:addflags(fileopts..clink.argmatcher():addarg({clink.filematches, "$stdin", "$stdout", hint="Expected for file-Options"})):nofiles()
:addarg({clink.filematches, hint=sdx_dl_hint_func})
:nofiles()

-- Arguments descriptions
:adddescriptions(
    { "-p", "--path",         description = "Path to download subtitles"},
    { "-q", "--quiet",        description = "No verbose mode" },
    { "-v", "--verbose",      description = "Be in verbose mode" },
    { "-h", "--help",         description = "Show help text" },
    { "-nc", "--no-choose",   description = "No Choose sub manually" },
    { "-nf", "--no-filter",   description = "Do not filter search results" },
    { "-nl", "--nlines",      description = "Show only nl availables records per screen" },
    { "-x", "--proxy",        description = "Set a http(s) proxy connection" },
    { "-S", "--Season",       description = "Search for Season" },
    { "-i", "--imdb",         description = "Search first for the IMDB id or title" },
    { "-t", "--title",        description = "Set the title of the show" },
    { "-k", "--keyword",      description = "Add keyword to search among subtitles"},
    { "-sx", "--SubX",        description = "Search using SubX API"},
    { "-f", "--force",        description = "override existing file"},
    { "-V", "--version",      description = "Show program version"},
    {"-vc", "--view-config",  description = "View config file"},
    {"-sc", "--save-config",  description = "Save options to config file"},
    {"-lc", "--load-config",  description = "Load config file options"},
    {"-c",  "--config",       description = "Save an option to config file"},
    {"-r",  "--reset",        description = "Reset an option in the config file"},
    {"-b",  "--bypass",       description = "Run bypass with options [force, manual]"},
    {"-cb",  "--conf-bypass", description = "Config bypass options"}
)