let s:plugin_root_dir = fnamemodify(resolve(expand('<sfile>:p')), ':h')

function! s:PowerThesaurus(...)
  let l:mode = a:0 ? a:1 : 'i'
  let l:line = getline('.')

  " Locate the start and end of the query terms based on whether we
  " started out in visual or insert mode (assumed by default).
  if l:mode == 'v'
    let l:start = col("'<") - 1
    let l:end = col("'>") - 1

    " Put the cursor exactly one character after the end of the visual
    " selection.  This is important to avoid partial replacement of the
    " word.
    call cursor(line('.'), col("'>") + 1)
  else
    let l:end = col(".") - 1

    " Move back until we find the fist non-alphabet character.
    let l:start = l:end
    while l:start > 0 && l:line[l:start - 1] =~ '\a'
      let l:start -= 1
    endwhile
  endif

  let l:base = l:line[l:start:l:end]

  echo "Querying powerthesaurus.org ..."

  " Run powerthesaurus.py and parse each line as a dictionary.
  let l:res = map(systemlist(s:plugin_root_dir . '/powerthesaurus.py ' . shellescape(l:base)), 
        \ {_, val -> eval(val)})

  " Fix the case of completion based on whether the first character of
  " the query is upper or lower.
  if l:base[0] =~# '[a-z]'
    for item in l:res
      let item['word'] = tolower(item['word'][0]) . item['word'][1:]
    endfor
  elseif l:base[0] =~# '[A-Z]'
    for item in l:res
      let item['word'] = toupper(item['word'][0]) . item['word'][1:]
    endfor
  endif

  " Now call the complete() function
  call complete(l:start + 1, l:res)

  " Kludge to avoid deleting the base word before selecting the first
  " item in the completion menu.  We do this by moving up the menu by
  " emulating the <C-p> keypress.
  call feedkeys("\<C-p>")

  return ''
endfunction

" Map <C-x><C-m> for our custom completion.
inoremap <silent> <C-x><C-m> <C-r>=<SID>PowerThesaurus('n')<CR>
vnoremap <silent> <C-x><C-m> <Esc>i<C-r>=<SID>PowerThesaurus('v')<CR>

" Make subsequent <C-m> presses after <C-x><C-m> go to the next entry (just like
" other <C-x>* mappings).
inoremap <expr> <C-m> pumvisible() ?  "\<C-n>" : "\<C-m>"
