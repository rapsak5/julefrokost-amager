// De syv fiskere. id skal matche framenavnene i atlasset (fisher/<id>/..., portrait/<id>).
// Udseendet (skæg, sydvest, pibe) ligger i tools/build_assets.py.

export const FISHERS = [
  { id: 'andreas', name: 'Andreas' },
  { id: 'anders', name: 'Anders' },
  { id: 'mark', name: 'Mark' },
  { id: 'claus', name: 'Claus' },
  { id: 'theis', name: 'Theis' },
  { id: 'kenni', name: 'Kenni' },
  { id: 'kasper', name: 'Kasper' },
];

export const DEFAULT_FISHER = 'kasper';

export function fisherById(id) {
  return FISHERS.find((f) => f.id === id) || FISHERS.find((f) => f.id === DEFAULT_FISHER);
}
