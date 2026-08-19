using System;
using System.Collections.Generic;
using System.Security.Cryptography;
using System.Text.Json;
using Tpm2Lib;

class Program
{
    private static readonly uint[] RequestedPcrs =
    {
        0, 2, 4, 7
    };

    static int Main(string[] args)
    {
        try
        {
            if (args.Length == 1 && args[0] == "pcr-read")
            {
                return RunPcrRead();
            }

            if (args.Length == 2 && args[0] == "quote")
            {
                return RunQuote(args[1]);
            }

            Console.Error.WriteLine(
                "Usage:\n" +
                "  tpm-helper pcr-read\n" +
                "  tpm-helper quote <64-char-hex-nonce>"
            );

            return 1;
        }
        catch (Exception ex)
        {
            Console.Error.WriteLine(
                JsonSerializer.Serialize(
                    new
                    {
                        error = true,
                        message = ex.Message
                    }
                )
            );

            return 2;
        }
    }


    static Tpm2 OpenTpm(out Tpm2Device device)
    {
        device = new TbsDevice();
        device.Connect();

        return new Tpm2(device);
    }


    static Dictionary<string, string> ReadPcrs(
        Tpm2 tpm,
        out PcrSelection[] actualSelection,
        out Tpm2bDigest[] values
    )
    {
        var requestedSelection = new[]
        {
            new PcrSelection(
                TpmAlgId.Sha256,
                RequestedPcrs
            )
        };

        tpm.PcrRead(
            requestedSelection,
            out actualSelection,
            out values
        );

        if (values.Length != RequestedPcrs.Length)
        {
            throw new Exception(
                $"Expected {RequestedPcrs.Length} PCR values, " +
                $"TPM returned {values.Length}"
            );
        }

        var pcrs = new Dictionary<string, string>();

        for (int i = 0; i < RequestedPcrs.Length; i++)
        {
            pcrs[RequestedPcrs[i].ToString()] =
                Convert
                    .ToHexString(values[i].buffer)
                    .ToLowerInvariant();
        }

        return pcrs;
    }


    static TpmHandle CreateAttestationKey(
        Tpm2 tpm,
        out TpmPublic akPublic
    )
    {
        var template = new TpmPublic(
            TpmAlgId.Sha256,

            ObjectAttr.Sign |
            ObjectAttr.Restricted |
            ObjectAttr.FixedTPM |
            ObjectAttr.FixedParent |
            ObjectAttr.SensitiveDataOrigin |
            ObjectAttr.UserWithAuth,

            null,

            new RsaParms(
                new SymDefObject(),
                new SchemeRsassa(TpmAlgId.Sha256),
                2048,
                0
            ),

            new Tpm2bPublicKeyRsa()
        );

        var sensitive = new SensitiveCreate(
            null,
            null
        );

        CreationData creationData;
        TkCreation creationTicket;
        byte[] creationHash;

        return tpm.CreatePrimary(
            TpmRh.Endorsement,
            sensitive,
            template,
            null,
            Array.Empty<PcrSelection>(),
            out akPublic,
            out creationData,
            out creationHash,
            out creationTicket
        );
    }


    static int RunPcrRead()
    {
        Tpm2Device device;
        var tpm = OpenTpm(out device);

        try
        {
            var pcrs = ReadPcrs(
                tpm,
                out _,
                out _
            );

            Console.WriteLine(
                JsonSerializer.Serialize(
                    new
                    {
                        mode = "real",
                        bank = "sha256",
                        pcrs
                    },
                    new JsonSerializerOptions
                    {
                        WriteIndented = true
                    }
                )
            );

            return 0;
        }
        finally
        {
            tpm.Dispose();
        }
    }


    static int RunQuote(string nonceHex)
    {
        if (nonceHex.Length != 64)
        {
            throw new ArgumentException(
                "Nonce must be exactly 32 bytes / 64 hex characters"
            );
        }

        byte[] nonce;

        try
        {
            nonce = Convert.FromHexString(nonceHex);
        }
        catch
        {
            throw new ArgumentException(
                "Nonce must contain hexadecimal characters only"
            );
        }

        Tpm2Device device;
        var tpm = OpenTpm(out device);

        TpmHandle? akHandle = null;

        try
        {
            akHandle = CreateAttestationKey(
                tpm,
                out TpmPublic akPublic
            );

            var pcrSelection = new[]
            {
                new PcrSelection(
                    TpmAlgId.Sha256,
                    RequestedPcrs
                )
            };

            ISignatureUnion quoteSignature;

            Attest quotedInfo = tpm.Quote(
                akHandle,
                nonce,
                new SchemeRsassa(TpmAlgId.Sha256),
                pcrSelection,
                out quoteSignature
            );

            var rsassaSignature =
                quoteSignature as SignatureRsassa;

            if (rsassaSignature == null)
            {
                throw new Exception(
                    "TPM returned unexpected signature type"
                );
            }

            var pcrs = ReadPcrs(
                tpm,
                out PcrSelection[] actualSelection,
                out Tpm2bDigest[] pcrValues
            );

            bool verifiedLocally =
                akPublic.VerifyQuote(
                    TpmAlgId.Sha256,
                    actualSelection,
                    pcrValues,
                    nonce,
                    quotedInfo,
                    quoteSignature
                );

            if (!verifiedLocally)
            {
                throw new Exception(
                    "TPM quote failed local verification"
                );
            }

            byte[] quoteBytes =
                quotedInfo.GetTpmRepresentation();

            byte[] akPublicBytes =
                akPublic.GetTpmRepresentation();

            byte[] akFingerprint =
                SHA256.HashData(akPublicBytes);

            string akId =
                "ak-sha256:" +
                Convert
                    .ToHexString(akFingerprint)
                    .ToLowerInvariant();

            var result = new
            {
                mode = "real",

                bank = "sha256",

                nonce = nonceHex.ToLowerInvariant(),

                pcrs,

                quote_b64 =
                    Convert.ToBase64String(
                        quoteBytes
                    ),

                signature_b64 =
                    Convert.ToBase64String(
                        rsassaSignature.sig
                    ),

                ak_public_b64 =
                    Convert.ToBase64String(
                        akPublicBytes
                    ),

                ak_id = akId,

                signature_algorithm =
                    "rsassa-sha256",

                verified_locally =
                    verifiedLocally
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

            return 0;
        }
        finally
        {
            if (akHandle != null)
            {
                try
                {
                    tpm.FlushContext(akHandle);
                }
                catch
                {
                }
            }

            tpm.Dispose();
        }
    }
}