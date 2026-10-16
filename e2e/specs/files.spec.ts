import { test, expect } from '@playwright/test';
import { FileManagerPage } from '../pages/FileManagerPage';

test.describe('Управление файлами (загрузка, скачивание, переименование, удаление)', () => {
  test.beforeEach(async ({ page }) => {
    const filePage = new FileManagerPage(page);
    await filePage.login('admin', 'admin12345');
    await filePage.goto();
  });

  test('Мультизагрузка файлов, переименование, скачивание и удаление', async ({ page }) => {
    const filePage = new FileManagerPage(page);
    const fileName1 = `doc_${Date.now()}.txt`;
    const fileName2 = `data_${Date.now()}.csv`;
    const renamedFile = `renamed_${Date.now()}.txt`;
    const filesTable = page.locator('table');

    await test.step('Загрузка двух файлов за один запрос', async () => {
      await filePage.uploadFiles([
        { name: fileName1, mimeType: 'text/plain', buffer: Buffer.from('Playwright Test Content 1') },
        { name: fileName2, mimeType: 'text/csv', buffer: Buffer.from('col1,col2\nval1,val2') },
      ]);
      await expect(filesTable.getByText(fileName1)).toBeVisible();
      await expect(filesTable.getByText(fileName2)).toBeVisible();
    });

    await test.step('Скачивание файла через page.waitForEvent("download")', async () => {
      const downloadPromise = page.waitForEvent('download');
      await page.getByTestId(`download-btn-${fileName1}`).click();
      const download = await downloadPromise;
      expect(download.suggestedFilename()).toBe(fileName1);
    });

    await test.step('Переименование файла', async () => {
      await filePage.renameItem(fileName1, renamedFile);
      await expect(filesTable.getByText(renamedFile)).toBeVisible();
      await expect(filesTable.getByText(fileName1)).not.toBeVisible();
    });

    await test.step('Удаление файлов с подтверждением', async () => {
      await filePage.deleteItem(renamedFile, true);
      await filePage.deleteItem(fileName2, true);
      await expect(filesTable.getByText(renamedFile)).not.toBeVisible();
      await expect(filesTable.getByText(fileName2)).not.toBeVisible();
    });
  });

  test('Загрузка файла превышающего лимит размера выдает валидационную ошибку (не 500)', async ({ page }) => {
    const filePage = new FileManagerPage(page);
    const oversizedFile = `large_${Date.now()}.bin`;
    // Лимит 10 МБ -> отправляем буфер 11 МБ
    const oversizedBuffer = Buffer.alloc(11 * 1024 * 1024, 0);

    await test.step('Попытка загрузки файла больше 10 МБ', async () => {
      await filePage.uploadFiles([
        { name: oversizedFile, mimeType: 'application/octet-stream', buffer: oversizedBuffer },
      ]);
      await expect(page).not.toHaveTitle(/Server Error/);
      await expect(filePage.flashMessage).toContainText('превышает допустимый лимит');
    });
  });
});