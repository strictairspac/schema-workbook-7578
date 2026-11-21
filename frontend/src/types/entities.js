/** Relation:{id,code,title,attributes,note}; Dependency:{id,relation_id,lhs,rhs,note}
 *  RulePeriod:{id,relation_id,effective_from,source:baseline|correction,correction_note,idempotency_key,entries:RuleEntry[]}
 *  RuleEntry:{id,period_id,lhs,rhs,note}
 *  Report:{id,name,relation_id,commission_date,input_snapshot{rule_provenance,...},status,result,error} */
export const entityNames=['relations','dependencies','rule_periods','rule_entries','reports'];
