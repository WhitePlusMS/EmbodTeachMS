import { spawnSync } from "node:child_process";
import { readFile, writeFile } from "node:fs/promises";
import { resolve } from "node:path";
import openapiTS, { astToString } from "openapi-typescript";
import ts from "typescript";

function run(command, args) {
  const result = spawnSync(command, args, {
    cwd: process.cwd(),
    env: process.env,
    shell: false,
    stdio: "inherit",
  });
  if (result.error !== undefined) {
    console.error(result.error.message);
  }
  if (result.status !== 0) {
    process.exit(result.status ?? 1);
  }
}

const backendPython = resolve(
  "..",
  "backend",
  ".venv",
  process.platform === "win32" ? "Scripts/python.exe" : "bin/python",
);

run(backendPython, [
  "../backend/scripts/export_openapi.py",
  "openapi.json",
]);

const schemaPath = resolve("openapi.json");
const outputPath = resolve("src/api/schema.d.ts");
const schema = JSON.parse(await readFile(schemaPath, "utf8"));
const ast = await openapiTS(schema, {
  // OpenAPI 的 binary string 在浏览器请求端对应 Blob，而不是普通字符串。
  transform(schemaObject) {
    if (schemaObject.type === "string" && schemaObject.format === "binary") {
      return ts.factory.createTypeReferenceNode("Blob");
    }
    return undefined;
  },
});

await writeFile(outputPath, astToString(ast), "utf8");
