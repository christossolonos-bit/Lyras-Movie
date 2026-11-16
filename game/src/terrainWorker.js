// Builds terrain tile meshes off the main thread.
import { tileData, farData } from './heightfield.js';

onmessage = (e) => {
  const { id, kind, tx, tz, segs, skirt, step } = e.data;
  const d = kind === 'far' ? farData(step) : tileData(tx, tz, segs, skirt);
  const transfer = [d.pos.buffer, d.nor.buffer, d.col.buffer, d.uv.buffer, d.idx.buffer];
  if (d.heights) transfer.push(d.heights.buffer);
  postMessage({ id, ...d }, transfer);
};
