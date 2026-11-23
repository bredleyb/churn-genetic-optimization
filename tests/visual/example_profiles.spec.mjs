import { test, expect } from '@playwright/test';

test('exemplos numerados preservam edições, restauro e limite de cinco', async ({ page }) => {
  await page.setViewportSize({width:1024,height:768});
  await page.goto('/', {waitUntil:'domcontentloaded'});
  const month = page.getByRole('textbox', {name:'Tempo como cliente'});
  const restore = page.getByRole('button', {name:'Restaurar perfil'});
  const deleteProfile = page.getByRole('button', {name:'Excluir perfil'});
  const first = page.getByRole('button', {name:'1',exact:true});
  const second = page.getByRole('button', {name:'2',exact:true});
  const plus = page.getByRole('button', {name:'+',exact:true});

  await expect(first).toBeVisible();
  await expect(second).toBeVisible();
  await expect(restore).toBeDisabled();
  await expect(deleteProfile).toBeDisabled();
  const topAlignment = await Promise.all([
    restore.boundingBox(),first.boundingBox(),deleteProfile.boundingBox(),
  ]);
  expect(Math.abs(topAlignment[0].height - topAlignment[1].height)).toBeLessThanOrEqual(1);
  expect(Math.abs(topAlignment[0].width - topAlignment[1].width)).toBeLessThanOrEqual(1);
  expect(Math.abs(topAlignment[0].y + topAlignment[0].height/2 -
                  topAlignment[1].y - topAlignment[1].height/2)).toBeLessThanOrEqual(2);
  expect(Math.abs(topAlignment[2].height - topAlignment[0].height)).toBeLessThanOrEqual(1);
  expect(Math.abs(topAlignment[2].width - topAlignment[0].width)).toBeLessThanOrEqual(1);
  expect(Math.abs(topAlignment[2].y + topAlignment[2].height/2 -
                  topAlignment[1].y - topAlignment[1].height/2)).toBeLessThanOrEqual(2);
  expect(topAlignment[2].x).toBeGreaterThan(topAlignment[0].x);
  const pristineColor = await restore.evaluate(el => getComputedStyle(el).backgroundColor);
  expect(pristineColor).toBe('rgb(0, 0, 0)');

  await second.click();
  await expect(second).toHaveAttribute('kind','primary');
  const secondOriginal = await month.inputValue();
  await plus.click();
  await expect(page.getByRole('button', {name:'3',exact:true})).toBeVisible();
  await expect(deleteProfile).toBeEnabled();
  await expect(month).toHaveValue(secondOriginal);
  await expect(restore).toBeDisabled();

  await month.click();
  await month.press('ControlOrMeta+A');
  for (const number of ['9','8','7']) await month.press(number);
  await expect(month).toHaveValue('987 meses');
  await expect(restore).toBeEnabled();
  await expect.poll(() => restore.evaluate(el => getComputedStyle(el).backgroundColor))
    .toBe('rgb(14, 16, 19)');
  await restore.hover();
  await expect.poll(() => restore.evaluate(el => getComputedStyle(el).backgroundColor))
    .toBe('rgb(32, 33, 36)');

  await first.click();
  await expect(month).toHaveValue('3 meses');
  await second.click();
  await expect(month).toHaveValue(secondOriginal);
  await page.getByRole('button', {name:'3',exact:true}).click();
  await expect(month).toHaveValue('987 meses');
  await restore.click();
  await expect(month).toHaveValue(secondOriginal);
  await expect(restore).toBeDisabled();

  await plus.click();
  await expect(page.getByRole('button', {name:'4',exact:true})).toBeVisible();
  await plus.click();
  await expect(page.getByRole('button', {name:'5',exact:true})).toBeVisible();
  await expect(plus).toHaveCount(0);
  await expect(page.locator('.st-key-dashboard-profile-choices [data-testid="stButton"] button'))
    .toHaveCount(5);
});

for (const viewport of [{width:1024,height:768},{width:390,height:900}]) {
  test('círculos e grade rápida respeitam o painel — '+viewport.width+'x'+viewport.height,
    async ({page}) => {
      await page.setViewportSize(viewport);
      await page.goto('/', {waitUntil:'domcontentloaded'});
      const choices = page.locator('.st-key-dashboard-profile-choices');
      const controls = choices.locator('[data-testid="stButton"] button');
      await expect(controls).toHaveCount(3);
      const frame = await choices.boundingBox();
      const restore = page.getByRole('button',{name:'Restaurar perfil'});
      const deleteProfile = page.getByRole('button',{name:'Excluir perfil'});
      const restoreBox = await restore.boundingBox();
      const deleteBox = await deleteProfile.boundingBox();
      const positions = await Promise.all((await controls.all()).map(button => button.boundingBox()));
      for (const rect of positions) {
        expect(Math.abs(rect.width - rect.height), 'Botão não é circular').toBeLessThanOrEqual(1);
        for (const [label, action] of [['Restaurar',restoreBox],['Excluir',deleteBox]]) {
          expect(Math.abs(rect.width - action.width), label+' com dimensão diferente')
            .toBeLessThanOrEqual(1);
          expect(Math.abs((rect.y+rect.height/2) - (action.y+action.height/2)),
            label+' desalinhado com os perfis').toBeLessThanOrEqual(2);
        }
        expect(rect.x, 'Botão passou do lado esquerdo').toBeGreaterThanOrEqual(frame.x - 2);
        expect(rect.x+rect.width, 'Botão passou do lado direito')
          .toBeLessThanOrEqual(frame.x+frame.width+2);
      }
      const actionFrame = await page.locator('.st-key-dashboard-profile-actions').boundingBox();
      for (const rect of [restoreBox,deleteBox]) {
        expect(rect.x).toBeGreaterThanOrEqual(actionFrame.x - 2);
        expect(rect.x + rect.width).toBeLessThanOrEqual(actionFrame.x + actionFrame.width + 2);
      }
      const squareRadius = await restore.evaluate(el =>
        parseFloat(getComputedStyle(el).borderTopLeftRadius));
      const circleRadius = await controls.first().evaluate(el =>
        parseFloat(getComputedStyle(el).borderTopLeftRadius));
      expect(squareRadius).toBe(4);
      expect(circleRadius).toBeGreaterThan(squareRadius + 3);
      const plus = page.getByRole('button', {name:'+',exact:true});
      for (let i=3; i<=5; i++) {
        await plus.click();
        await expect(page.getByRole('button', {name:String(i),exact:true})).toBeVisible();
      }
      await expect(plus).toHaveCount(0);
      const full = await choices.boundingBox();
      const five = await Promise.all((await choices.locator('[data-testid="stButton"] button').all())
        .map(button => button.boundingBox()));
      expect(five).toHaveLength(5);
      for (const rect of five) {
        expect(rect.x).toBeGreaterThanOrEqual(full.x - 2);
        expect(rect.x + rect.width).toBeLessThanOrEqual(full.x + full.width + 2);
      }
      const quick = page.locator('.st-key-dashboard-quick-fields');
      const columns = quick.locator('[data-testid="stHorizontalBlock"] > [data-testid="stColumn"]');
      await expect(columns).toHaveCount(4);
      const boxes = await Promise.all((await columns.all()).map(column => column.boundingBox()));
      for (const [a,b] of [[0,2],[1,3]]) {
        expect(Math.abs(boxes[a].x-boxes[b].x)).toBeLessThanOrEqual(2);
        expect(Math.abs(boxes[a].width-boxes[b].width)).toBeLessThanOrEqual(2);
      }
      // A medida de cada controle deve coincidir com sua coluna, inclusive
      // o componente Streamlit v2 de meses, que tem um shadow root próprio.
      const fields = [
        quick.locator('.n3-tenure-field'),
        quick.locator('[data-testid="stSelectbox"]:has(input[aria-label="Tipo de contrato"]) [role="group"]'),
        quick.locator('[data-testid="stSelectbox"]:has(input[aria-label="Serviço de internet"]) [role="group"]'),
        quick.locator('[data-testid="stNumberInput"]:has(input[aria-label="Cobrança mensal"]) [data-baseweb="input"]'),
      ];
      const sizes = await Promise.all(fields.map(field => field.boundingBox()));
      for (const [a,b] of [[0,2],[1,3]]) {
        expect(Math.abs(sizes[a].x-sizes[b].x), 'Campos desalinhados em X')
          .toBeLessThanOrEqual(2);
        expect(Math.abs(sizes[a].width-sizes[b].width), 'Campos com larguras diferentes')
          .toBeLessThanOrEqual(2);
      }
      for (let i = 0; i < 4; i++) {
        expect(Math.abs(sizes[i].width-boxes[i].width), 'Campo não preenche a coluna')
          .toBeLessThanOrEqual(2);
      }
    });
}


test('exclusão direta preserva os exemplos protegidos', async ({page}) => {
  await page.setViewportSize({width:1024,height:768});
  await page.goto('/', {waitUntil:'domcontentloaded'});
  const first = page.getByRole('button',{name:'1',exact:true});
  const second = page.getByRole('button',{name:'2',exact:true});
  const add = page.getByRole('button',{name:'+',exact:true});
  const remove = page.getByRole('button',{name:'Excluir perfil'});

  await expect(remove).toBeDisabled();
  await second.click();
  await expect(remove).toBeDisabled();
  await add.click();
  await expect(remove).toBeEnabled();
  await remove.click();
  await expect(page.getByRole('dialog',{name:'Excluir exemplo'})).toHaveCount(0);
  await expect(page.getByRole('button',{name:'3',exact:true})).toHaveCount(0);
  await expect(second).toHaveAttribute('kind','primary');
  await expect(remove).toBeDisabled();
  await expect(add).toBeVisible();
  await expect(first).toBeVisible();
});

test('exclusão intermediária renumera sem perder dados e reabre a criação', async ({page}) => {
  await page.setViewportSize({width:1024,height:768});
  await page.goto('/', {waitUntil:'domcontentloaded'});
  const add = page.getByRole('button',{name:'+',exact:true});
  const remove = page.getByRole('button',{name:'Excluir perfil'});
  const tenure = page.getByRole('textbox',{name:'Tempo como cliente'});
  const setMonths = async value => {
    await tenure.click();
    await tenure.press('ControlOrMeta+A');
    for (const digit of value) await tenure.press(digit);
    await expect(tenure).toHaveValue(value+' meses');
  };
  await add.click(); // Exemplo 3, fotografia com 3 meses
  await setMonths('30');
  await add.click(); // Exemplo 4, fotografia com 30 meses
  await setMonths('40');
  await add.click(); // Exemplo 5, fotografia com 40 meses
  await setMonths('50');
  await expect(add).toHaveCount(0);

  await page.getByRole('button',{name:'4',exact:true}).click();
  await expect(tenure).toHaveValue('40 meses');
  await remove.click();
  await expect(page.getByRole('dialog',{name:'Excluir exemplo'})).toHaveCount(0);
  await expect(page.getByRole('button',{name:'3',exact:true})).toHaveAttribute('kind','primary');
  await expect(tenure).toHaveValue('30 meses');
  await expect(page.getByRole('button',{name:'5',exact:true})).toHaveCount(0);
  await expect(add).toBeVisible();
  await page.getByRole('button',{name:'4',exact:true}).click();
  await expect(tenure).toHaveValue('50 meses');
  await page.getByRole('button',{name:'Restaurar perfil'}).click();
  await expect(tenure).toHaveValue('40 meses');
  await add.click();
  await expect(page.getByRole('button',{name:'5',exact:true})).toBeVisible();
});
