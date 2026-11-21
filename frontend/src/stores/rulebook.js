import {rulebookApi} from '../api/rulebook.js';
export const rulebookStore={
  periods:[],coverage:[],
  idemKey:'corr-'+Date.now(),
  rotateKey(){this.idemKey='corr-'+Date.now().toString(36)+Math.random().toString(16).slice(2,8);},
  forRelation(relationId){return this.periods.filter(p=>p.relation_id===relationId)
    .sort((a,b)=>a.effective_from.localeCompare(b.effective_from));},
  latest(relationId){const chain=this.forRelation(relationId);return chain[chain.length-1]||null;},
  async refresh(){const data=await rulebookApi.list();this.periods=data.periods;this.coverage=data.coverage;return data;}
};
