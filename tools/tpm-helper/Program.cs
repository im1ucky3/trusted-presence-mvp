using System;
using System.Collections.Generic;
using System.Text.Json;
using Tpm2Lib;

class Program
{
    static int Main(string[] args)
    {
        if (args.Length != 1 || args[0] != "pcr-read")
        {
            Console.Error.WriteLine(
                "Usage: tpm-helper pcr-read"
            );

            return 1;
        }

        Tpm2Device device = new TbsDevice();

        try
        {
            device.Connect();

            var tpm = new Tpm2(device);

            uint[] requestedPcrs =
            {
                0,
                2,
                4,
                7
            };

            var selection = new[]
            {
                new PcrSelection(
                    TpmAlgId.Sha256,
                    requestedPcrs
                )
            };

            tpm.PcrRead(
                selection,
                out PcrSelection[] readSelection,
                out Tpm2bDigest[] values
            );

            if (values.Length != requestedPcrs.Length)
            {
                throw new Exception(
                    $"Expected {requestedPcrs.Length} PCRs, " +
                    $"but TPM returned {values.Length}"
                );
            }

            var pcrs = new Dictionary<string, string>();

            for (int i = 0; i < requestedPcrs.Length; i++)
            {
                string hex =
                    Convert
                        .ToHexString(values[i].buffer)
                        .ToLowerInvariant();

                pcrs[
                    requestedPcrs[i].ToString()
                ] = hex;
            }

            var result = new
            {
                mode = "real",
                bank = "sha256",
                pcrs = pcrs
            };

            Console.WriteLine(
                JsonSerializer.Serialize(
                    result,
                    new JsonSerializerOptions
                    {
                        WriteIndented = true
                    }
                )
            );

            tpm.Dispose();

            return 0;
        }
        catch (Exception ex)
        {
            var error = new
            {
                error = true,
                message = ex.Message
            };

            Console.Error.WriteLine(
                JsonSerializer.Serialize(error)
            );

            return 2;
        }
    }
}