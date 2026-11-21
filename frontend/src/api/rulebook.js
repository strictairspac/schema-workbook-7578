import {api} from './client.js';
export const rulebookApi={
  list:(relationId)=>api('/rule-periods'+(relationId?`?relation_id=${relationId}`:'')),
  baseline:data=>api('/rule-periods/baseline','POST',data),
  correct:data=>api('/rule-periods/corrections','POST',data),
  effective:(relationId,onDate)=>api(`/rule-periods/effective?relation_id=${relationId}&on_date=${onDate}`)
};
