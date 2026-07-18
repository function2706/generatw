using System;
using System.Collections.Concurrent;
using System.Net.Sockets;
using System.Text;
using System.Threading;

namespace MinorShift.Emuera.Runtime.Utils.Generatw;

/// <summary>
/// generatw (画像生成アプリ) との連携用に, 画面テキストを TCP で push するエミッタ.
///
/// Emuera は TCP クライアントとして 127.0.0.1:&lt;port&gt; へ接続し, 画面確定時
/// (ClipboardProcessor と同じトリガ) の可視テキストを送る.
/// メッセージフレーム: 4byte 長さ (big-endian, 符号なし) + UTF-8 本文.
///
/// 送信はすべてバックグラウンドのワーカースレッドで best-effort に行い,
/// 接続失敗・切断・例外はすべて握り潰してゲーム進行を一切阻害しない.
/// アプリ未起動時は送信が黙って捨てられる.
/// </summary>
public static class GeneratwEmitter
{
	// 画面テキストは「最新の状態のみ」重要なので, 詰まった場合は古いものを捨てる.
	private const int QueueCapacity = 64;

	private static readonly object gate = new();
	private static BlockingCollection<string> queue;
	private static Thread worker;
	private static volatile bool started;

	private static string host = "127.0.0.1";
	private static int port = 52340;

	private static TcpClient client;
	private static NetworkStream stream;

	/// <summary>
	/// エミッタを起動する (多重起動は無視). Config 確定後に一度呼ぶ.
	/// </summary>
	public static void Start(string emitHost, int emitPort)
	{
		lock (gate)
		{
			if (started) return;
			host = string.IsNullOrEmpty(emitHost) ? "127.0.0.1" : emitHost;
			port = emitPort;
			queue = new BlockingCollection<string>(QueueCapacity);
			worker = new Thread(WorkerLoop)
			{
				IsBackground = true,
				Name = "GeneratwEmitter",
			};
			started = true;
			worker.Start();
		}
	}

	/// <summary>
	/// 画面テキストを送信キューへ積む. 未起動なら何もしない.
	/// キューが一杯の場合は古いものを捨てて最新を優先する.
	/// </summary>
	public static void Send(string text)
	{
		if (!started || text == null) return;
		var q = queue;
		if (q == null) return;

		if (!q.TryAdd(text))
		{
			// 詰まっている: 古いものを 1 件捨てて最新を入れ直す (best-effort)
			q.TryTake(out _);
			q.TryAdd(text);
		}
	}

	/// <summary>
	/// 終了処理. ワーカーを止めて接続を閉じる.
	/// </summary>
	public static void Stop()
	{
		lock (gate)
		{
			if (!started) return;
			started = false;
			try { queue?.CompleteAdding(); } catch (Exception) { }
		}
	}

	private static void WorkerLoop()
	{
		try
		{
			foreach (var text in queue.GetConsumingEnumerable())
			{
				TrySend(text);
			}
		}
		catch (Exception)
		{
			// GetConsumingEnumerable が CompleteAdding 等で抜ける場合を含め, 握り潰す
		}
		finally
		{
			CloseConnection();
		}
	}

	private static void TrySend(string text)
	{
		try
		{
			EnsureConnected();
			if (stream == null) return;

			byte[] body = Encoding.UTF8.GetBytes(text);
			byte[] frame = new byte[4 + body.Length];
			// 4byte big-endian 符号なし長さ (Python 側 struct ">I" と一致)
			uint len = (uint)body.Length;
			frame[0] = (byte)((len >> 24) & 0xFF);
			frame[1] = (byte)((len >> 16) & 0xFF);
			frame[2] = (byte)((len >> 8) & 0xFF);
			frame[3] = (byte)(len & 0xFF);
			Buffer.BlockCopy(body, 0, frame, 4, body.Length);

			stream.Write(frame, 0, frame.Length);
		}
		catch (Exception)
		{
			// 送信失敗: 接続を破棄し, 次回再接続を試みる
			CloseConnection();
		}
	}

	private static void EnsureConnected()
	{
		if (client != null && client.Connected && stream != null) return;

		CloseConnection();
		try
		{
			client = new TcpClient();
			// 相手 (アプリ) 不在時に長時間ブロックしないよう即時接続を試みる
			var ar = client.BeginConnect(host, port, null, null);
			if (!ar.AsyncWaitHandle.WaitOne(TimeSpan.FromMilliseconds(300)))
			{
				CloseConnection();
				return;
			}
			client.EndConnect(ar);
			client.NoDelay = true;
			stream = client.GetStream();
		}
		catch (Exception)
		{
			CloseConnection();
		}
	}

	private static void CloseConnection()
	{
		try { stream?.Dispose(); } catch (Exception) { }
		try { client?.Close(); } catch (Exception) { }
		stream = null;
		client = null;
	}
}
