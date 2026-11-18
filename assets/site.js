document.documentElement.classList.add('js')

const toggle = document.querySelector('.nav-toggle')
const navigation = document.querySelector('#primary-nav')

function closeNavigation() {
  if (!toggle || !navigation) return
  navigation.classList.remove('is-open')
  toggle.setAttribute('aria-expanded', 'false')
  toggle.textContent = 'Menu'
}

if (toggle && navigation) {
  toggle.hidden = false
  toggle.addEventListener('click', () => {
    const open = toggle.getAttribute('aria-expanded') !== 'true'
    navigation.classList.toggle('is-open', open)
    toggle.setAttribute('aria-expanded', String(open))
    toggle.textContent = open ? 'Close menu' : 'Menu'
  })
  navigation.addEventListener('click', event => {
    if (event.target.closest('a')) closeNavigation()
  })
  document.addEventListener('keydown', event => {
    if (event.key === 'Escape' && toggle.getAttribute('aria-expanded') === 'true') {
      closeNavigation()
      toggle.focus()
    }
  })
  window.matchMedia('(min-width: 761px)').addEventListener('change', closeNavigation)
}

const controls = document.querySelector('[data-filter-controls]')
if (controls) {
  const buttons = [...controls.querySelectorAll('[data-filter]')]
  const projects = [...document.querySelectorAll('.project-row[data-categories]')]
  const status = controls.querySelector('.filter-status')
  controls.hidden = false
  for (const button of buttons) {
    button.addEventListener('click', () => {
      const filter = button.dataset.filter
      let visible = 0
      for (const project of projects) {
        const show = filter === 'all' || project.dataset.categories.split(' ').includes(filter)
        project.hidden = !show
        if (show) visible++
      }
      for (const option of buttons) option.setAttribute('aria-pressed', String(option === button))
      status.textContent = `Showing ${visible} ${visible === 1 ? 'item' : 'items'}`
    })
  }
}
