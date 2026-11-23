import {test,expect} from '@playwright/test';
import {openClient,tabs,fieldGroup,clickOption,replaceMonths,measure,near,screenshot,ensureNoException} from './client.helpers.mjs';
import tenureRenderer,{clampMonths,displayMonths,replaceMonthDigits} from '../../src/tenure_control.mjs';

test('CL-F01 mês singular/plural, limites e substituição numérica sem afetar unidade',()=>{
  expect([0,1,2,999].map(displayMonths)).toEqual(['0 meses','1 mês','2 meses','999 meses']);
  expect(clampMonths(-1)).toBe(0);
  expect(clampMonths(1000)).toBe(999);
  expect(clampMonths(1.8)).toBe(1);
  expect(replaceMonthDigits(24,0,2,'5')).toBe(5);
  expect(replaceMonthDigits(24,2,2,'abc')).toBe(24);
  expect(replaceMonthDigits(2,1,1,'9999')).toBe(999);
});

test('CL-F02 editor de meses tem um único texto protegido e stepper correto',async({page},info)=>{
  await openClient(page,{width:1024,height:768});
  const months=page.getByRole('textbox',{name:'Tempo como cliente'});
  const field=page.locator('.n3-tenure-field');
  const minus=page.getByRole('button',{name:'Diminuir um mês'});
  const plus=page.getByRole('button',{name:'Aumentar um mês'});
  await expect(months).toHaveValue('3 meses');
  await plus.click();
  await expect(months).toHaveValue('4 meses');
  await minus.click();
  await expect(months).toHaveValue('3 meses');
  await replaceMonths(page,1);
  await expect(months).toHaveValue('1 mês');
  await months.click();
  await months.press('End');
  await expect.poll(async()=>months.evaluate(el=>el.selectionStart)).toBe(1);
  await months.press('Delete');
  await expect(months).toHaveValue('1 mês');
  await months.press('ArrowRight');
  await expect.poll(async()=>months.evaluate(el=>el.selectionStart)).toBe(1);
  await replaceMonths(page,0);
  await expect(minus).toBeDisabled();
  await expect(plus).toBeEnabled();
  await replaceMonths(page,999);
  await expect(plus).toBeDisabled();
  await expect(minus).toBeEnabled();
  await months.click();
  const focus=await field.evaluate(el=>({
    shadow:getComputedStyle(el).boxShadow,border:getComputedStyle(el).borderColor,
    width:el.getBoundingClientRect().width,
  }));
  expect(focus.shadow).toContain('inset');
  expect(focus.border).toBe('rgb(245, 245, 245)');
  expect(focus.width).toBeGreaterThan(60);
  await screenshot(page,info,'CL-F02-meses-foco-e-limite');
});

test('CL-F03 categorias representam apenas os dados do dataset',async({page})=>{
  await openClient(page,{width:1024,height:768});
  await tabs(page).getByRole('tab',{name:'Perfil'}).click();
  await page.getByRole('combobox',{name:'Gênero'}).click();
  const options=page.getByRole('option');
  await expect(options).toHaveCount(2);
  await expect(page.getByRole('option',{name:'Feminino'})).toBeVisible();
  await expect(page.getByRole('option',{name:'Masculino'})).toBeVisible();
  await page.getByRole('option',{name:'Masculino'}).click();
  await expect(page.getByRole('combobox',{name:'Gênero'})).toHaveValue('Masculino');
  await clickOption(page,'Pessoa idosa','Sim');
  await clickOption(page,'Possui parceiro(a)','Sim');
  await clickOption(page,'Possui dependentes','Sim');
  const extras=tabs(page).getByRole('tab',{name:'Extras'});
  await extras.click();
  await expect(extras,'A aba Extras deve permanecer ativa após editar o Perfil')
    .toHaveAttribute('aria-selected','true');
  await clickOption(page,'Streaming de filmes','Sim');
  await tabs(page).getByRole('tab',{name:'Perfil'}).click();
  await expect(page.getByRole('combobox',{name:'Gênero'})).toHaveValue('Masculino');
  await expect(page.getByRole('combobox',{name:'Possui dependentes'})).toHaveValue('Sim');
  await ensureNoException(page);
});

test('CL-F04 telefonia e internet sincronizam campos dependentes',async({page})=>{
  await openClient(page,{width:1024,height:768});
  await tabs(page).getByRole('tab',{name:'Serviços'}).click();
  await clickOption(page,'Serviço de telefone','Não');
  const lines=page.getByRole('combobox',{name:'Múltiplas linhas telefônicas'});
  await expect(lines).toHaveValue('Sem serviço telefônico');
  await expect(lines).toBeDisabled();
  await clickOption(page,'Serviço de telefone','Sim');
  await expect(lines).toBeEnabled();
  await expect(lines).toHaveValue('Não');
  await clickOption(page,'Serviço de internet','Não');
  for(const name of ['Segurança online','Backup online','Proteção de dispositivos']){
    const field=page.getByRole('combobox',{name});
    await expect(field).toHaveValue('Sem serviço de internet');
    await expect(field).toBeDisabled();
  }
  await tabs(page).getByRole('tab',{name:'Extras'}).click();
  for(const name of ['Suporte técnico','Streaming de TV','Streaming de filmes']){
    const field=page.getByRole('combobox',{name});
    await expect(field).toBeDisabled();
    await expect(field).toHaveValue('Sem serviço de internet');
  }
  await clickOption(page,'Serviço de internet','DSL');
  for(const name of ['Suporte técnico','Streaming de TV','Streaming de filmes']){
    await expect(page.getByRole('combobox',{name})).toBeEnabled();
  }
  await ensureNoException(page);
});

test('CL-F05 campos de cobrança e total indisponível conservam tipos',async({page})=>{
  await openClient(page,{width:1024,height:768});
  const charge=page.getByRole('spinbutton',{name:'Cobrança mensal'});
  // type=number guarda o ponto no DOM; a apresentação visual pode usar vírgula.
  await expect(charge).toHaveValue('95.50');
  await charge.fill('101.50');
  await charge.press('Tab');
  await tabs(page).getByRole('tab',{name:'Conta'}).click();
  const missing=page.getByRole('checkbox',{name:'Total cobrado indisponível'});
  const total=page.getByRole('spinbutton',{name:'Total cobrado'});
  await expect(total).toBeEnabled();
  // O checkbox React Aria recebe o clique no rótulo associado. Clicar no
  // input interno faz o Playwright enfrentar a sobreposição esperada do label.
  await page.getByText('Total cobrado indisponível',{exact:true}).click();
  await expect(missing).toBeChecked();
  await expect(total).toBeDisabled();
  await missing.focus();
  await missing.press('Space');
  await expect(missing).not.toBeChecked();
  await expect(total).toBeEnabled();
  await tabs(page).getByRole('tab',{name:'Perfil'}).click();
  await expect(charge).toHaveValue('101.50');
});


test('CL-F06 cores, raios, tipografia e hover dos steppers são compartilhados',
  async({page})=>{
    await openClient(page,{width:1024,height:768});
    const tenure=page.locator('.n3-tenure-field');
    const internet=fieldGroup(page,'Serviço de internet');
    // No Streamlit instalado, o wrapper real é stNumberInputContainer
    // (React Aria). O seletor antigo data-baseweb=input inexiste.
    const charges=page.locator(
      '[data-testid="stNumberInput"]:has(input[aria-label="Cobrança mensal"]) [data-testid="stNumberInputContainer"]');
    for(const [label,element] of [['Tempo',tenure],['Internet',internet],['Cobrança',charges]]){
      const v=await element.evaluate(el=>{
        const style=getComputedStyle(el);
        return {background:style.backgroundColor,radius:style.borderTopLeftRadius,
          height:el.getBoundingClientRect().height};
      });
      expect(v.background,label+' tem fundo divergente').toBe('rgb(14, 16, 19)');
      expect(v.radius,label+' tem arredondamento divergente').toBe('4px');
      near(v.height,42,label+' altura',2);
    }
    const timeInput=page.getByRole('textbox',{name:'Tempo como cliente'});
    const monthlyInput=page.getByRole('spinbutton',{name:'Cobrança mensal'});
    const values=await Promise.all([timeInput,monthlyInput].map(el=>el.evaluate(node=>({
      font:getComputedStyle(node).fontSize,color:getComputedStyle(node).color,
    }))));
    for(const v of values){
      expect(v.font).toBe('14px');
      expect(v.color).toBe('rgb(245, 245, 245)');
    }
    const plus=page.locator('.n3-tenure-field button[data-step="1"]');
    const minus=page.locator('.n3-tenure-field button[data-step="-1"]');
    const arrow=page.locator('.st-key-dashboard-quick-fields [data-testid="stSelectbox"]')
      .first().getByRole('button',{name:'Open'});
    for(const [name,control] of [['mais',plus],['menos',minus],['seletor',arrow]]){
      await expect(control,name+' cor do ícone').toHaveCSS('color','rgb(216, 216, 216)');
      await control.hover();
      await expect(control,name+' hover').toHaveCSS('background-color','rgb(32, 33, 36)');
      await page.mouse.move(0,0);
      await expect(control,name+' retorno').toHaveCSS('background-color','rgb(14, 16, 19)');
    }
  });

for(const size of [
  {width:1440,height:900},{width:1366,height:768},
  {width:1280,height:720},{width:1024,height:768},
  {width:768,height:900},{width:390,height:900},
]){
  test('CL-F07 Cobrança exibe − e + em '+size.width+'x'+size.height,
    async({page})=>{
      await openClient(page,size);
      const numberWidget=page.locator(
        '[data-testid="stNumberInput"]:has(input[aria-label="Cobrança mensal"])');
      const stepButtons=numberWidget.locator('button:visible');
      await expect(stepButtons,
        'Cobrança sem controles − e + em '+size.width+'px')
        .toHaveCount(2,{timeout:6000});
      const colors=await Promise.all((await stepButtons.all()).map(control=>
        control.evaluate(el=>getComputedStyle(el).color)));
      expect(colors).toEqual(['rgb(216, 216, 216)','rgb(216, 216, 216)']);
      for(const control of await stepButtons.all()){
        await control.hover();
        await expect(control).toHaveCSS('background-color','rgb(32, 33, 36)');
        await page.mouse.move(0,0);
        await expect(control).toHaveCSS('background-color','rgb(14, 16, 19)');
      }
    });
}

test('CL-F08 edição imediata após stepper não perde seleção por reposicionamento do caret',
  async({page})=>{
    await openClient(page,{width:1024,height:768});
    const value=page.getByRole('textbox',{name:'Tempo como cliente'});
    await page.getByRole('button',{name:'Aumentar um mês'}).click();
    await page.getByRole('button',{name:'Diminuir um mês'}).click();
    await value.click();
    await value.press('ControlOrMeta+A');
    await value.press('1');
    await expect(value,
      'O caret voltou ao fim dos dígitos antes da substituição, produzindo 31 meses')
      .toHaveValue('1 mês',{timeout:1500});
});


test('CL-F09 componente v2 mantém seleção quando chega um rerun antigo',async({page})=>{
  // O componente recebe código REAL importado do módulo, com callbacks v2
  // simulados apenas para reproduzir a ordem de eventos sem treinar modelos.
  const source = {
    clamp:clampMonths.toString(),display:displayMonths.toString(),
    replace:replaceMonthDigits.toString(),renderer:tenureRenderer.toString(),
  };
  await page.setContent(
    '<div class="n3-tenure"><input type="text" aria-label="Tempo como cliente" />'+
    '<button data-step="-1" aria-label="Diminuir um mês">−</button>'+
    '<button data-step="1" aria-label="Aumentar um mês">+</button></div>');
  await page.evaluate(src=>{
    const js=[
      'const clampMonths = ('+src.clamp+');',
      'const displayMonths = ('+src.display+');',
      'const replaceMonthDigits = ('+src.replace+');',
      'return ('+src.renderer+');',
    ].join('\n');
    const mount = new Function(js)();
    window.n3Mount = value => {
      window.n3Cleanup?.();
      window.n3Cleanup=mount({
        parentElement:document.querySelector('.n3-tenure').parentElement,
        data:{value},setStateValue:()=>{},
      });
    };
    window.n3Mount(3);
  },source);
  const input=page.getByRole('textbox',{name:'Tempo como cliente'});
  await page.getByRole('button',{name:'Aumentar um mês'}).click();
  await page.getByRole('button',{name:'Diminuir um mês'}).click();
  await input.click();
  await input.press('ControlOrMeta+A');
  await expect.poll(()=>input.evaluate(el=>[el.selectionStart,el.selectionEnd]))
    .toEqual([0,1]);

  // Resposta atrasada do Streamlit sobre o mesmo elemento montado com key:
  // o Python ainda contém 4 meses, mas o editor já está em 3 selecionado.
  await page.evaluate(()=>window.n3Mount(4));
  await expect(input).toHaveValue('3 meses');
  await expect.poll(()=>input.evaluate(el=>[el.selectionStart,el.selectionEnd]))
    .toEqual([0,1]);
  await expect(input).toHaveAttribute('data-select-all-digits','true');
  // Reproduz a falha observada no Streamlit real: a seleção pode colapsar
  // entre Ctrl+A e beforeinput embora a intenção do usuário permaneça.
  await input.evaluate(el=>el.setSelectionRange(1,1));
  await expect.poll(()=>input.evaluate(el=>[el.selectionStart,el.selectionEnd]))
    .toEqual([1,1]);
  await input.press('1');
  await expect(input).toHaveValue('1 mês');
  await expect(input).not.toHaveAttribute('data-select-all-digits','true');
  await expect.poll(()=>input.evaluate(el=>[el.selectionStart,el.selectionEnd]))
    .toEqual([1,1]);
  // Fora da edição, uma atualização externa legítima deve voltar a prevalecer.
  await page.getByRole('button',{name:'Aumentar um mês'}).click();
  await page.evaluate(()=>window.n3Mount(7));
  await expect(input).toHaveValue('7 meses');

  // O Streamlit também pode trocar o nó DOM inteiro enquanto o usuário
  // mantém Ctrl+A ativo. O host deve preservar a intenção entre montagens.
  await input.click();
  await input.press('ControlOrMeta+A');
  await expect(input).toHaveAttribute('data-select-all-digits','true');
  await page.evaluate(()=>{
    const old=document.querySelector('.n3-tenure');
    const replacement=old.cloneNode(true);
    // O novo input perde seu estado local, como numa remontagem real.
    replacement.querySelector('input').removeAttribute('data-select-all-digits');
    old.replaceWith(replacement);
    window.n3Mount(7);
  });
  await expect(input).toHaveValue('7 meses');
  await input.press('1');
  await expect(input).toHaveValue('1 mês');
  await expect(input).not.toHaveAttribute('data-select-all-digits','true');
});
