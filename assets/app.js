const state = { snapshot: null, selectedId: null };
const $ = (selector) => document.querySelector(selector);

function element(tag, className, text) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text !== undefined) node.textContent = text;
  return node;
}

function percent(value) {
  return value == null ? '—' : `${(value * 100).toFixed(1).replace('.', ',')}%`;
}

function gameDate(value) {
  return new Intl.DateTimeFormat('pt-BR', { day: '2-digit', month: 'short', timeZone: 'America/Fortaleza' }).format(new Date(value)).replace('.', '').toUpperCase();
}

function updateSummary() {
  const { teams, scheduled_games: scheduled } = state.snapshot;
  const ranked = teams.filter((team) => team.sos !== null);
  const hardest = ranked[0];
  const easiest = ranked[ranked.length - 1];
  $('#hardest-team').textContent = hardest?.name || '—';
  $('#hardest-score').textContent = hardest ? `${percent(hardest.sos)} de índice SOS` : 'Sem jogos futuros';
  $('#easiest-team').textContent = easiest?.name || '—';
  $('#easiest-score').textContent = easiest ? `${percent(easiest.sos)} de índice SOS` : 'Sem jogos futuros';
  $('#remaining-games').textContent = scheduled;
  $('#season-label').textContent = `TEMPORADA ${state.snapshot.season}`;
  const updated = new Intl.DateTimeFormat('pt-BR', { dateStyle: 'long', timeStyle: 'short', timeZone: 'America/Fortaleza' }).format(new Date(state.snapshot.updated_at));
  $('#refresh-label').textContent = `Dados atualizados em ${updated} (Fortaleza)`;
  $('#footer-updated').textContent = `Última coleta: ${updated} (horário de Fortaleza).`;
  $('#standings-link').href = state.snapshot.sources.standings;
  const ageHours = (Date.now() - new Date(state.snapshot.updated_at).getTime()) / 3600000;
  if (ageHours > 48) {
    $('#refresh-label').textContent += ' · Snapshot antigo';
    $('#refresh-label').classList.add('stale');
  }
}

function teamBadge(team) {
  const badge = element('span', 'team-badge', team.abbreviation.slice(0, 3));
  if (team.logo) {
    const image = element('img');
    image.src = team.logo;
    image.alt = '';
    image.loading = 'lazy';
    image.onerror = () => image.remove();
    badge.prepend(image);
  }
  return badge;
}

function renderRanking() {
  const tbody = $('#ranking-body');
  tbody.replaceChildren();
  const query = $('#search').value.trim().toLocaleLowerCase('pt-BR');
  const teams = [...state.snapshot.teams];
  if ($('#sort').value === 'easiest') teams.reverse();
  const filtered = teams.filter((team) => team.name.toLocaleLowerCase('pt-BR').includes(query) || team.abbreviation.toLocaleLowerCase('pt-BR').includes(query));
  if (!filtered.length) {
    const row = element('tr');
    const cell = element('td', 'table-message', 'Nenhum clube encontrado.');
    cell.colSpan = 6;
    row.append(cell);
    tbody.append(row);
    return;
  }
  for (const team of filtered) {
    const originalRank = state.snapshot.teams.findIndex((item) => item.id === team.id) + 1;
    const row = element('tr', team.id === state.selectedId ? 'selected' : '');
    row.append(element('td', 'rank-cell', String(originalRank).padStart(2, '0')));
    const nameCell = element('td');
    const teamButton = element('button', 'team-button');
    teamButton.type = 'button';
    teamButton.append(teamBadge(team), element('span', '', team.name));
    teamButton.addEventListener('click', () => selectTeam(team.id, true));
    nameCell.append(teamButton);
    row.append(nameCell);
    const sosCell = element('td');
    const score = element('div', 'score-cell');
    score.append(element('strong', '', percent(team.sos)));
    const bar = element('span', 'score-track');
    const fill = element('span', 'score-fill');
    fill.style.width = `${Math.min(100, (team.sos || 0) * 100)}%`;
    bar.append(fill);
    score.append(bar);
    sosCell.append(score);
    row.append(sosCell);
    row.append(element('td', 'games-count', String(team.next_games.length).padStart(2, '0')));
    const opponentsCell = element('td');
    const opponents = element('div', 'opponent-list');
    team.next_games.forEach((game) => {
      const chip = element('span', `opponent-chip ${game.location === 'casa' ? 'at-home' : 'away'}`);
      chip.title = `${game.opponent} · ${game.location} · força ${percent(game.difficulty)}`;
      chip.append(element('b', '', game.opponent_abbreviation), element('small', '', game.location === 'casa' ? 'C' : 'F'));
      opponents.append(chip);
    });
    opponentsCell.append(opponents);
    row.append(opponentsCell);
    const actionCell = element('td', 'action-cell');
    actionCell.append(element('span', 'row-arrow', '↗'));
    row.append(actionCell);
    tbody.append(row);
  }
}

function selectTeam(id, scroll) {
  state.selectedId = id;
  const team = state.snapshot.teams.find((item) => item.id === id);
  $('#detail-title').textContent = team.name;
  $('#detail-subtitle').textContent = `${team.next_games.length} próximos jogos · ${team.remaining} restantes no campeonato · ${team.points} pontos em ${team.played} partidas`;
  $('#detail-score').textContent = percent(team.sos);
  const grid = $('#game-grid');
  grid.replaceChildren();
  for (const [index, game] of team.next_games.entries()) {
    const opponent = state.snapshot.teams.find((item) => item.id === game.opponent_id);
    const side = game.location === 'casa' ? 'away' : 'home';
    const venueRecord = opponent.venue[side];
    const card = element('article', 'game-card');
    const top = element('div', 'game-top');
    top.append(element('span', '', `JOGO ${String(index + 1).padStart(2, '0')}`), element('span', '', gameDate(game.date)));
    card.append(top);
    const opponentLine = element('div', 'game-opponent');
    opponentLine.append(teamBadge(opponent), element('strong', '', opponent.name));
    card.append(opponentLine);
    card.append(element('span', `venue-tag ${game.location === 'casa' ? 'at-home' : 'away'}`, game.location === 'casa' ? 'EM CASA' : 'FORA DE CASA'));
    const scoreLine = element('div', 'game-score');
    scoreLine.append(element('span', '', 'FORÇA DO ADVERSÁRIO'), element('b', '', percent(game.difficulty)));
    card.append(scoreLine);
    const track = element('div', 'game-track');
    const fill = element('span');
    fill.style.width = `${game.difficulty * 100}%`;
    track.append(fill);
    card.append(track);
    card.append(element('p', 'game-explanation', `${venueRecord.points} pontos em ${venueRecord.played} jogos ${side === 'home' ? 'em casa' : 'fora'}; ajustado pela campanha geral.`));
    grid.append(card);
  }
  if (!team.next_games.length) grid.append(element('p', 'no-games', 'Este clube não tem jogos futuros no calendário.'));
  renderRanking();
  if (scroll) $('#detalhes').scrollIntoView({ behavior: 'smooth', block: 'start' });
}

async function load() {
  try {
    const response = await fetch('data/processed/snapshot.json', { cache: 'no-store' });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const snapshot = await response.json();
    if (!Array.isArray(snapshot.teams) || !snapshot.teams.length) throw new Error('Snapshot sem clubes');
    state.snapshot = snapshot;
    updateSummary();
    selectTeam(snapshot.teams[0].id, false);
  } catch (error) {
    $('#ranking-body').replaceChildren();
    const row = element('tr');
    const cell = element('td', 'table-message', 'Não foi possível carregar o ranking.');
    cell.colSpan = 6;
    row.append(cell);
    $('#ranking-body').append(row);
    const notice = $('#page-error');
    notice.hidden = false;
    notice.textContent = `Falha ao abrir o snapshot (${error.message}). Execute python -m http.server 8000 na pasta do projeto e acesse http://localhost:8000. Para atualizar: python -m radar_sos.`;
  }
}

$('#search').addEventListener('input', () => state.snapshot && renderRanking());
$('#sort').addEventListener('change', () => state.snapshot && renderRanking());
load();
