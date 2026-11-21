export function formValues(form, numbers=[]){const values=Object.fromEntries(new FormData(form));for(const key of numbers)values[key]=Number(values[key]);return values;}
const split=s=>s.split(/[,，]/).map(x=>x.trim()).filter(Boolean);
/** 解析多行规则文本，每行格式：决定项(逗号分隔) -> 被决定项(逗号分隔)；空决定项表示常量依赖。 */
export function parseRuleLines(text){
  const entries=[];const errors=[];
  text.split(/\n+/).map(x=>x.trim()).filter(Boolean).forEach((line,idx)=>{
    if(!line.includes('->')){errors.push(`第${idx+1}行缺少 -> 分隔符`);return;}
    const [left,right]=line.split('->').map(x=>x.trim());
    const rhs=split(right);
    if(!rhs.length){errors.push(`第${idx+1}行被决定项为空`);return;}
    entries.push({lhs:split(left),rhs,note:''});
  });
  if(!entries.length)errors.push('至少填写一条规则');
  return {entries,errors};
}
