set nocompatible
filetype off
set rtp+=~/.vim/bundle/Vundle.vim
call vundle#begin()

Plugin 'VundleVim/Vundle.vim'
call vundle#end()
filetype plugin indent on

set hlsearch
set incsearch
set ignorecase
set smartcase


colorscheme molokai
set t_Co=256
filetype indent on
set autoindent
set shiftwidth=4
set softtabstop=4
set tabstop=4
set expandtab
set smarttab

set lazyredraw

set encoding=utf-8
set linebreak
set scrolloff=1
set sidescrolloff=5
syntax enable
set wrap

set laststatus=2
set ruler
set wildmenu
set number
set noerrorbells
set mouse=a
set title
set background=dark

set foldmethod=indent
set foldnestmax=3

set autoread
set backspace=indent,eol,start
set nobackup
set history=1000
set nomodeline
set noswapfile
set spell
