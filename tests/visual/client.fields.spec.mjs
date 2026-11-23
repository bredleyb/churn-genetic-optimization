import {test,expect} from '@playwright/test';
import {openClient,tabs,fieldGroup,clickOption,replaceMonths,expectMonths,measure,near,screenshot,ensureNoException} from './client.helpers.mjs';
import tenureRenderer,{clampMonths,displayMonths,parseMonthInput} from '../../src/tenure_control.mjs';

test('CL-F01 números, limites e unidade não editável',()=>{
  expect([0,1,2,999].map(displayMonths)).toEqual(['0 meses','1 mês','2 meses','999 meses']);
  expect(clampMonths(-1)).toBe(0);
  expect(clampMonths(1000)).toBe(999);
  expect(clampMonths(1.8)).toBe(1);
  expect(parseMonthInput('24')).toBe(24);
  expect(parseMonthInput('001')).toBe(1);
  expect(parseMonthInput('999')).toBe(999);
  for(const bad of ['','24 meses','-1','abc','1000'])
    expect(parseMonthInput(bad)).toBeNull();
});

test('CL-F02 editor de meses tem um único texto protegido e stepper correto',async({page},info)=>{
  await openClient(page,{width:1024,height:768});
  const months=page.getByRole('textbox',{name:'Tempo como cliente'});
  const field=page.locator('.n3-tenure-field');
  const minus=page.getByRole('button',{name:'Diminuir um mês'});
  const plus=page.getByRole('button',{name:'Aumentar um mês'});
  await expectMonths(page,3);
  await plus.click();
  await expectMonths(page,4);
  await minus.click();
  await expectMonths(page,3);
  await replaceMonths(page,1);
  await expectMonths(page,1);
  await months.click();
  await months.press('End');
  await expect.poll(async()=>months.evaluate(el=>el.selectionStart)).toBe(1);
  await months.press('Delete');
  await expectMonths(page,1);
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
    border:getComputedStyle(el).borderColor,
    width:el.getBoundingClientRect().width,
    ring:getComputedStyle(el,'::after').borderTopColor,
    ringWidth:getComputedStyle(el,'::after').borderTopWidth,
    ringZ:Number(getComputedStyle(el,'::after').zIndex),
    ringPointer:getComputedStyle(el,'::after').pointerEvents,
  }));
  expect(focus.border).toBe('rgb(245, 245, 245)');
  expect(focus.ring).toBe('rgb(245, 245, 245)');
  expect(focus.ringWidth).toBe('2px');
  expect(focus.ringZ).toBeGreaterThanOrEqual(3);
  expect(focus.ringPointer).toBe('none');
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
      'Ctrl+A seguido de 1 deve substituir o número, sem concatenar dígitos')
      .toHaveValue('1',{timeout:1500});
    await expect(page.locator('.n3-tenure-unit')).toHaveText('mês');
});


test('CL-F09 componente v2 preserva edição nativa durante reruns e revisões',async({page})=>{
  // Integra a implementação real com um host v2 mínimo, sem algoritmo genético.
  const source={
    clamp:clampMonths.toString(),display:displayMonths.toString(),
    parse:parseMonthInput.toString(),renderer:tenureRenderer.toString(),
  };
  await page.setContent(
    '<div class="n3-tenure"><label for="n3-tenure-value">Tempo como cliente</label>'+
    '<div class="n3-tenure-field">'+
    '<input id="n3-tenure-value" type="text" inputmode="numeric" maxlength="3" '+
    'aria-label="Tempo como cliente" aria-describedby="n3-tenure-unit"/>'+
    '<span id="n3-tenure-unit" class="n3-tenure-unit"> meses</span>'+
    '<span class="n3-tenure-spacer"></span>'+
    '<button data-step="-1" aria-label="Diminuir um mês">−</button>'+
    '<button data-step="1" aria-label="Aumentar um mês">+</button></div></div>');
  await page.evaluate(src=>{
    const js=[
      'const clampMonths = ('+src.clamp+');',
      'const displayMonths = ('+src.display+');',
      'const parseMonthInput = ('+src.parse+');',
      'const ACTIVE_MOUNT = Symbol.for("n3.tenure.activeMount");',
      'return ('+src.renderer+');',
    ].join('\n');
    const mount = new Function(js)();
    window.received=[];
    window.n3Mount=value=>{
      window.n3Cleanup?.();
      window.n3Cleanup=mount({
        parentElement:document.body,data:{value},
        setStateValue:(name,val)=>window.received.push([name,val]),
      });
    };
    window.n3Mount(3);
  },source);
  const input=page.getByRole('textbox',{name:'Tempo como cliente'});
  await expectMonths(page,3);
  await page.getByRole('button',{name:'Aumentar um mês'}).click();
  await page.getByRole('button',{name:'Diminuir um mês'}).click();
  await expectMonths(page,3);
  await input.click();
  await input.press('ControlOrMeta+A');
  await expect.poll(()=>input.evaluate(el=>[el.selectionStart,el.selectionEnd]))
    .toEqual([0,1]);
  // O backend ainda devolve 4 meses, enquanto o usuário edita 3.
  await page.evaluate(()=>window.n3Mount(4));
  await expectMonths(page,3);
  await expect.poll(()=>input.evaluate(el=>[el.selectionStart,el.selectionEnd]))
    .toEqual([0,1]);
  await input.press('1');
  await expectMonths(page,1);
  await expect.poll(()=>input.evaluate(el=>[el.selectionStart,el.selectionEnd]))
    .toEqual([1,1]);
  await expect.poll(()=>page.evaluate(()=>window.received.at(-1)))
    .toEqual(['value',1]);

  // Fora do foco, uma atualização externa legítima deve prevalecer.
  await page.getByRole('button',{name:'Aumentar um mês'}).click();
  await page.evaluate(()=>window.n3Mount(7));
  await expectMonths(page,7);
  // Nova revisão pode trocar o nó: edição posterior continua nativa.
  await page.evaluate(()=>{
    const previous=document.querySelector('.n3-tenure');
    previous.replaceWith(previous.cloneNode(true));
    window.n3Mount(7);
  });
  await expectMonths(page,7);
  await input.click();
  await input.press('ControlOrMeta+A');
  await input.press('1');
  await expectMonths(page,1);
});

for(const width of [1440,390]){
  test('CL-F10 número e unidade compartilham caixa sem compartilhar seleção '+width,
    async({page})=>{
      await openClient(page,{width,height:900});
      const input=page.getByRole('textbox',{name:'Tempo como cliente'});
      const unit=page.locator('.n3-tenure-unit');
      const field=page.locator('.n3-tenure-field');
      await expectMonths(page,3);
      await expect(input).toHaveAttribute('maxlength','3');
      await expect(input).toHaveAttribute('inputmode','numeric');
      await expect(field.locator('input')).toHaveCount(1);
      const numberBox=await measure(input),unitBox=await measure(unit),
        fieldBox=await measure(field);
      near(numberBox.right,unitBox.left,'sufixo junto ao número',2);
      expect(numberBox.left).toBeGreaterThan(fieldBox.left);
      expect(unitBox.right).toBeLessThan(fieldBox.right-60);
      await input.click();
      await input.press('ControlOrMeta+A');
      await expect.poll(()=>input.evaluate(el=>[el.selectionStart,el.selectionEnd]))
        .toEqual([0,1]);
      await input.press('1');
      await expectMonths(page,1);
      const suffixAfter=await measure(unit);
      near(suffixAfter.left,unitBox.left,'unidade não desloca o campo',2);
      // O span deve ficar um pixel abaixo da referência vertical do
      // input nativo, alinhando a base do texto sem mexer nos dígitos.
      const baseline=await input.evaluate(el=>{
        const suffix=el.parentElement.querySelector('.n3-tenure-unit');
        const inputStyle=getComputedStyle(el);
        const unitStyle=getComputedStyle(suffix);
        return {
          valueY:new DOMMatrixReadOnly(inputStyle.transform).m42,
          unitY:new DOMMatrixReadOnly(unitStyle.transform).m42,
          sameFontSize:inputStyle.fontSize===unitStyle.fontSize,
          sameLineHeight:inputStyle.lineHeight===unitStyle.lineHeight,
        };
      });
      expect(baseline.sameFontSize).toBe(true);
      expect(baseline.sameLineHeight).toBe(true);
      near(baseline.unitY-baseline.valueY,1,'base da unidade alinhada ao valor',0.15);
    });
}


test('CL-F11 colagem, caracteres inválidos e rascunho vazio usam edição nativa',
  async({page})=>{
    await openClient(page,{width:1024,height:768});
    const input=page.getByRole('textbox',{name:'Tempo como cliente'});
    await replaceMonths(page,8);
    await input.press('a');
    await expectMonths(page,8); // caractere não numérico bloqueado
    const paste=text=>input.evaluate((el,source)=>{
      const clipboard=new DataTransfer();
      clipboard.setData('text/plain',source);
      el.dispatchEvent(new ClipboardEvent('paste',{
        bubbles:true,cancelable:true,clipboardData:clipboard,
      }));
    },text);
    await input.press('ControlOrMeta+A');
    await paste('24 meses');
    await expectMonths(page,24);
    await input.press('ControlOrMeta+A');
    await paste('1 mês');
    await expectMonths(page,1);
    await input.press('ControlOrMeta+A');
    await input.press('Backspace');
    await expect(input).toHaveValue('');
    await page.getByRole('button',{name:'Aumentar um mês'}).focus();
    await expectMonths(page,0);
    await expect(page.getByRole('button',{name:'Diminuir um mês'})).toBeDisabled();
  });


test('CL-F12 remontar sem cleanup não duplica listeners nem executa colagem duas vezes',
  async ({page})=>{
    const source={
      clamp:clampMonths.toString(),display:displayMonths.toString(),
      parse:parseMonthInput.toString(),renderer:tenureRenderer.toString(),
    };
    await page.setContent(
      '<div class="n3-tenure"><label for="n3-tenure-value">Tempo como cliente</label>'+
      '<div class="n3-tenure-field">'+
      '<input id="n3-tenure-value" type="text" inputmode="numeric" maxlength="3" '+
      'aria-label="Tempo como cliente" aria-describedby="n3-tenure-unit"/>'+
      '<span id="n3-tenure-unit" class="n3-tenure-unit"> meses</span>'+
      '<span class="n3-tenure-spacer"></span>'+
      '<button type="button" data-step="-1" aria-label="Diminuir um mês">−</button>'+
      '<button type="button" data-step="1" aria-label="Aumentar um mês">+</button>'+
      '</div></div>');
    await page.evaluate(src=>{
      const mount=new Function(
        'const clampMonths = ('+src.clamp+');\n'+
        'const displayMonths = ('+src.display+');\n'+
        'const parseMonthInput = ('+src.parse+');\n'+
        'const ACTIVE_MOUNT = Symbol.for("n3.tenure.activeMount");\n'+
        'return ('+src.renderer+');')();
      window.values=[];
      window.mountMonth=value=>mount({
        parentElement:document.body,
        data:{value},
        setStateValue:(name,value)=>window.values.push([name,value]),
      });
      // Reproduz uma montagem nova que chega antes do cleanup anterior.
      window.firstCleanup=window.mountMonth(8);
      window.secondCleanup=window.mountMonth(8);
      // NÃO executar firstCleanup aqui: a primeira colagem precisa
      // revelar se as duas instâncias ainda estão escutando o mesmo evento.
    },source);
    const input=page.getByRole('textbox',{name:'Tempo como cliente'});
    const paste=text=>input.evaluate((el,source)=>{
      const clipboard=new DataTransfer();
      clipboard.setData('text/plain',source);
      el.dispatchEvent(new ClipboardEvent('paste',{
        bubbles:true,cancelable:true,clipboardData:clipboard,
      }));
    },text);
    await expectMonths(page,8);
    await input.click();
    await input.press('ControlOrMeta+A');
    await paste('24 meses');
    await expectMonths(page,24);
    await expect.poll(()=>page.evaluate(()=>window.values))
      .toEqual([['value',24]]);
    // Cleanup de uma instância antiga não pode cancelar a mais recente.
    await page.evaluate(()=>window.firstCleanup());

    // Uma terceira montagem também deve substituir a segunda.
    await page.evaluate(()=>{
      window.thirdCleanup=window.mountMonth(24);
      window.secondCleanup(); // cleanup antigo fora de ordem
    });
    await input.press('ControlOrMeta+A');
    await paste('1 mês');
    await expectMonths(page,1);
    await expect.poll(()=>page.evaluate(()=>window.values))
      .toEqual([['value',24],['value',1]]);
  });


for(const viewport of [{width:1440,height:900},{width:390,height:900}]){
  test('CL-F13 foco, curvatura e hover exclusivo do Tempo '+viewport.width,
    async({page},info)=>{
      await openClient(page,viewport);
      const field=page.locator('.n3-tenure-field');
      const months=page.getByRole('textbox',{name:'Tempo como cliente'});
      const minus=page.getByRole('button',{name:'Diminuir um mês'});
      const plus=page.getByRole('button',{name:'Aumentar um mês'});
      const bg='rgb(14, 16, 19)',hover='rgb(32, 33, 36)';
      await months.click();
      await expect(field).toHaveCSS('border-color','rgb(245, 245, 245)');
      const visual=await field.evaluate(el=>{
        const css=getComputedStyle(el),ring=getComputedStyle(el,'::after');
        return {clip:css.overflowX,position:css.position,
          radius:css.borderTopRightRadius,layer:Number(ring.zIndex),
          pointer:ring.pointerEvents,color:ring.borderTopColor,
          width:ring.borderTopWidth,round:ring.borderTopRightRadius};
      });
      expect(visual).toMatchObject({
        clip:'hidden',position:'relative',radius:'4px',layer:3,
        pointer:'none',color:'rgb(245, 245, 245)',
        width:'2px',round:'4px',
      });
      await plus.hover();
      await expect(plus).toHaveCSS('background-color',hover);
      await expect(minus).toHaveCSS('background-color',bg);
      await expect(plus).toHaveAttribute('data-n3-pointer-hover','true');
      await plus.click();
      await expectMonths(page,4);
      await expect(plus).toHaveCSS('background-color',bg);
      await expect(minus).toHaveCSS('background-color',bg);
      await expect(plus).not.toHaveAttribute('data-n3-pointer-hover','true');
      await expect(minus).not.toHaveAttribute('data-n3-pointer-hover','true');
      await expect(field).toHaveCSS('border-color','rgb(245, 245, 245)');
      await screenshot(page,info,'CL-F13-foco-sem-hover-vizinho-'+viewport.width);
      await minus.hover();
      await expect(minus).toHaveCSS('background-color',hover);
      await expect(plus).toHaveCSS('background-color',bg);
      await minus.click();
      await expectMonths(page,3);
      await expect(minus).toHaveCSS('background-color',bg);
      await expect(plus).toHaveCSS('background-color',bg);
      await page.mouse.move(0,0);
      await expect(minus).toHaveCSS('background-color',bg);
      await expect(plus).toHaveCSS('background-color',bg);
    });
  test('CL-F14 foco e hover exclusivo da Cobrança '+viewport.width,
    async({page},info)=>{
      await openClient(page,viewport);
      const number=page.locator(
        '[data-testid="stNumberInput"]:has(input[aria-label="Cobrança mensal"])');
      const container=number.locator('[data-testid="stNumberInputContainer"]');
      const steppers=number.locator('button:visible');
      await expect(steppers).toHaveCount(2);
      const first=steppers.nth(0),second=steppers.nth(1);
      const bg='rgb(14, 16, 19)',hover='rgb(32, 33, 36)';
      await number.getByRole('spinbutton',{name:'Cobrança mensal'}).focus();
      const visual=await container.evaluate(el=>{
        const css=getComputedStyle(el),ring=getComputedStyle(el,'::after');
        return {clip:css.overflowX,position:css.position,radius:css.borderTopRightRadius,
          layer:Number(ring.zIndex),pointer:ring.pointerEvents,
          color:ring.borderTopColor,width:ring.borderTopWidth,round:ring.borderTopRightRadius};
      });
      expect(visual).toMatchObject({
        clip:'hidden',position:'relative',radius:'4px',layer:3,
        pointer:'none',color:'rgb(245, 245, 245)',width:'2px',round:'4px',
      });
      await first.hover();
      await expect(first).toHaveCSS('background-color',hover);
      await expect(second).toHaveCSS('background-color',bg);
      await first.click();
      await expect(first).toHaveCSS('background-color',bg);
      await expect(second).toHaveCSS('background-color',bg);
      await expect(first).not.toHaveAttribute('data-n3-pointer-hover','true');
      await expect(second).not.toHaveAttribute('data-n3-pointer-hover','true');
      await screenshot(page,info,'CL-F14-cobranca-foco-hover-'+viewport.width);
      await second.hover();
      await expect(second).toHaveCSS('background-color',hover);
      await expect(first).toHaveCSS('background-color',bg);
      await second.click();
      await expect(first).toHaveCSS('background-color',bg);
      await expect(second).toHaveCSS('background-color',bg);
      await page.mouse.move(0,0);
      await expect(first).toHaveCSS('background-color',bg);
      await expect(second).toHaveCSS('background-color',bg);
    });
}
