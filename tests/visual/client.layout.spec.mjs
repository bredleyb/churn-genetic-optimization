import {test,expect} from '@playwright/test';
import {VIEWPORTS,openClient,client,fields,footer,action,tabs,profileCircles,profileActions,fieldGroup,measure,near,screenshot,ensureNoException} from './client.helpers.mjs';

for(const size of VIEWPORTS){
  test('CL-L01 geometria e capturas '+size.width+'x'+size.height,async({page},info)=>{
    await openClient(page,size);
    const panel=await measure(client(page)),scroll=await measure(fields(page));
    const foot=await measure(footer(page)),btn=await measure(action(page));
    const edge = 12;
    const workspace = await measure(page.locator('.st-key-dashboard-workspace'));
    near(panel.left,edge,'padding externo esquerdo',2);
    near(panel.top,edge,'padding superior do dashboard',2);
    if(size.width<1024){
      near(workspace.left,panel.left,'painéis empilhados',2);
      near(workspace.right,panel.right,'largura dos painéis',2);
      near(workspace.top-panel.bottom,12,'intervalo vertical',2);
      if(size.width<700) near(panel.height,Math.min(744,size.height-24),'altura móvel',2);
      else expect(panel.height).toBeGreaterThan(400);
    }else{
      near(size.width-workspace.right,edge,'padding externo direito do dashboard',2);
      near(size.height-workspace.bottom,edge,'padding inferior do dashboard',2);
      near(panel.width,366,'largura Cliente desktop',2);
      near(panel.top,workspace.top,'painéis compartilham o topo',2);
      near(panel.bottom,workspace.bottom,'painéis compartilham a base',2);
      near(workspace.left-panel.right,12,'intervalo horizontal',2);
    }
    const pageOverflow=await page.evaluate(()=>({
      x:document.documentElement.scrollWidth-window.innerWidth,
      y:document.documentElement.scrollHeight-window.innerHeight,
    }));
    expect(pageOverflow.x,'overflow horizontal da página').toBeLessThanOrEqual(2);
    expect(pageOverflow.y,'overflow vertical da página').toBeLessThanOrEqual(2);
    expect(foot.bottom).toBeLessThanOrEqual(panel.bottom+1);
    expect(btn.left).toBeGreaterThan(scroll.left+7);
    expect(btn.right).toBeLessThan(scroll.right-7);
    expect(btn.height).toBe(48);
    await expect(profileCircles(page)).toHaveCount(3);
    await expect(profileActions(page)).toHaveCount(2);
    const label=await measure(page.locator('.churn-profile-label'));
    const first=await measure(profileCircles(page).first());
    near(label.left,btn.left,'rótulo do perfil',2);
    near(first.left,btn.left,'círculos',2);
    const acts=await Promise.all((await profileActions(page).all()).map(measure));
    for(const [i,rect] of acts.entries()){
      near(rect.width,first.width,'dimensão ação '+i,1);
      near(rect.height,first.height,'altura ação '+i,1);
      near(rect.cy,first.cy,'eixo ação '+i,2);
    }
    expect(acts[0].left).toBeLessThan(acts[1].left);
    const radii=await Promise.all([profileCircles(page).first(),...await profileActions(page).all()]
      .map(el=>el.evaluate(node=>parseFloat(getComputedStyle(node).borderTopLeftRadius))));
    expect(radii[0]).toBeGreaterThan(radii[1]+3);
    near(radii[1],4,'restaurar quadrado',1);near(radii[2],4,'excluir quadrado',1);

    const tenure=await measure(page.locator('.n3-tenure-field'));
    const contract=await measure(fieldGroup(page,'Tipo de contrato'));
    const internet=await measure(fieldGroup(page,'Serviço de internet'));
    const charge=await measure(page.locator(
      '[data-testid="stNumberInput"]:has(input[aria-label="Cobrança mensal"]) [data-testid="stNumberInputContainer"]'));
    const clientContentWidth=await client(page).evaluate(el=>{
      const css=getComputedStyle(el);
      return el.clientWidth-parseFloat(css.paddingLeft)-parseFloat(css.paddingRight);
    });
    if(clientContentWidth<=335){
      near(tenure.left,contract.left,'Campo rápido empilhado posição',2);
      near(tenure.width,contract.width,'Campo rápido empilhado largura',2);
    }else{
      expect(contract.left,
        'Em largura suficiente, campos rápidos devem ocupar duas colunas')
        .toBeGreaterThan(tenure.right+2);
    }
    near(tenure.left,internet.left,'Tempo/Serviço posição',2);
    near(tenure.width,internet.width,'Tempo/Serviço largura',2);
    near(contract.left,charge.left,'Contrato/Cobrança posição',2);
    near(contract.width,charge.width,'Contrato/Cobrança largura',2);
    near(tenure.left,btn.left,'início dos campos',2);
    near(charge.right,btn.right,'fim dos campos',2);
    for(const rect of [tenure,contract,internet,charge]){
      near(rect.height,42,'altura padronizada',2);
      expect(rect.right).toBeLessThanOrEqual(scroll.right-6);
    }
    if(size.width>=700&&size.width<1024){
      expect(contract.left).toBeGreaterThan(tenure.right);
      near(tenure.top,contract.top,'campos rápidos tablet',2);
    }
    const heading=await measure(page.getByRole('heading',{name:'Cliente',exact:true}));
    near(heading.cx,panel.cx,'título centralizado',2);
    // Rótulos devem manter uma linha: se quebrarem, os campos rápidos
    // deixam de formar duas linhas horizontalmente alinhadas.
    for(const label of ['Tipo de contrato','Cobrança mensal']){
      const node=page.locator('.st-key-dashboard-quick-fields [data-testid="stWidgetLabel"] p')
        .filter({hasText:label}).first();
      const rectangle=await measure(node);
      expect(rectangle.height,label+' quebrou em múltiplas linhas')
        .toBeLessThanOrEqual(21);
    }
    const colors=await client(page).evaluate(el=>({
      surface:getComputedStyle(el).backgroundColor,
      border:getComputedStyle(el).borderColor,
      title:getComputedStyle(el.querySelector('.churn-panel-heading')).color,
    }));
    expect(colors).toEqual({
      surface:'rgb(14, 16, 19)',border:'rgb(85, 88, 93)',title:'rgb(85, 88, 93)'});
    await ensureNoException(page);
    await screenshot(page,info,'CL-L01-inicial-'+size.width+'x'+size.height);
  });
  test('CL-L02 abas e área útil '+size.width+'x'+size.height,async({page},info)=>{
    await openClient(page,size);
    const btn=await measure(action(page));
    const labels={'Perfil':'Gênero','Conta':'Método de pagamento',
      'Serviços':'Serviço de telefone','Extras':'Streaming de filmes'};
    await expect(tabs(page).getByRole('tab')).toHaveCount(4);
    for(const [name,label] of Object.entries(labels)){
      await tabs(page).getByRole('tab',{name,exact:true}).click();
      await expect(tabs(page).getByRole('tab',{name,exact:true}))
        .toHaveAttribute('aria-selected','true');
      const group=fieldGroup(page,label);
      await expect(group).toBeVisible();
      const rect=await measure(group);
      near(rect.left,btn.left,name+' margem esquerda',2);
      near(rect.right,btn.right,name+' margem direita',2);
      near(rect.height,42,name+' altura',2);
      expect(await fields(page).evaluate(el=>el.scrollWidth-el.clientWidth),
        name+' overflow horizontal').toBeLessThanOrEqual(2);
      await expect(action(page)).toBeVisible();
      await ensureNoException(page);
      if(name==='Perfil'||name==='Serviços')
        await screenshot(page,info,'CL-L02-'+name+'-'+size.width+'x'+size.height);
    }
  });
}
test('CL-L03 tipografia, alinhamento vertical e hover dos seletores',async({page})=>{
  await openClient(page,{width:1024,height:768});
  const loaded=await page.evaluate(async()=>{
    await document.fonts.load('400 14px "Familjen Grotesk"');
    return Array.from(document.fonts).some(f=>
      f.family.replace(/["']/g,'').trim()==='Familjen Grotesk'&&f.status==='loaded');
  });
  expect(loaded,'Fonte Familjen Grotesk não carregada').toBe(true);
  const selects=page.locator('.st-key-dashboard-client [data-testid="stSelectbox"]:visible');
  expect(await selects.count()).toBeGreaterThanOrEqual(5);
  for(const el of await selects.all()){
    const geom=await el.evaluate(root=>{
      const lab=root.querySelector('[data-testid="stWidgetLabel"]');
      const title=lab?.querySelector('p'),input=root.querySelector('input[role="combobox"]');
      const group=root.querySelector('[role="group"]');
      if(!lab||!title||!input||!group)return null;
      const a=lab.getBoundingClientRect(),b=title.getBoundingClientRect();
      const c=input.getBoundingClientRect(),d=group.getBoundingClientRect();
      return {labelFont:getComputedStyle(title).fontSize,valueFont:getComputedStyle(input).fontSize,
        labelCenter:b.y+b.height/2-a.y-a.height/2,
        valueCenter:c.y+c.height/2-d.y-d.height/2};
    });
    expect(geom).toBeTruthy();
    expect(geom.labelFont).toBe('15px');expect(geom.valueFont).toBe('14px');
    expect(Math.abs(geom.labelCenter)).toBeLessThanOrEqual(2);
    expect(Math.abs(geom.valueCenter)).toBeLessThanOrEqual(2);
  }
  const arrow=page.locator('.st-key-dashboard-quick-fields [data-testid="stSelectbox"]')
    .first().getByRole('button',{name:'Open'});
  await expect(arrow).toHaveCSS('background-color','rgb(14, 16, 19)');
  await arrow.hover();
  await expect(arrow).toHaveCSS('background-color','rgb(32, 33, 36)');
  await page.mouse.move(0,0);
  await expect(arrow).toHaveCSS('background-color','rgb(14, 16, 19)');
});
test('CL-L04 abas mantém navegação por teclado e foco visível',async({page})=>{
  await openClient(page,{width:1024,height:768});
  const tab=tabs(page).getByRole('tab',{name:'Serviços'});
  await tab.focus();await expect(tab).toBeFocused();
  const style=await tab.evaluate(el=>({
    outline:getComputedStyle(el).outlineStyle,shadow:getComputedStyle(el).boxShadow}));
  expect(style.outline).toBe('none');
  // A marca de aba selecionada é um sublinhado interno (0px -2px).
  // Procurar "2px 0px 0px" também acusa esse sublinhado legítimo.
  expect(style.shadow).toContain('0px -2px 0px 0px inset');
  expect(style.shadow).not.toContain(' 2px 0px 0px 0px inset');
  expect(style.shadow).not.toContain(' -2px 0px 0px 0px inset');
  await tab.press('Enter');
  await expect(tab).toHaveAttribute('aria-selected','true');
});
